from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from config import Config
from mysql_connection import get_connection
from mysql.connector import Error
from datetime import datetime
import boto3

# 포스팅 하기
class PostingListResource(Resource) :
    @jwt_required()
    def post(self) :

        file = request.files.get("photo")
        content = request.form.get("content")
        user_id = get_jwt_identity()

        if file is None :
            return {"error" : "파일이 없습니다."}, 400
        
        current_time = datetime.now()

        new_file_name = current_time.isoformat().replace(":", "_") + str(user_id) + ".jpg"

        file.filename = new_file_name

        s3 = boto3.client("s3", aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)

        try :
            s3.upload_fileobj(file, Config.S3_BUCKET, file.filename, 
                              ExtraArgs = {"ACL" : "public-read",
                                           "ContentType" : "image/jpeg"})

        except Exception as e :
            print(e)
            return {"error" : str(e)}, 500
        
        # rekognition 서비스를 이용해서 object detection 하여,
        # 태그(label) 이름을 가져 온다.

        tag_list = self.detect_labels(new_file_name, Config.S3_BUCKET)
        print(tag_list)

        try :
            connection = get_connection()

            # 1. posting 테이블에 데이터를 넣어준다.
            query = '''
                    insert into posting
                    (userId, imageUrl, content)
                    values
                    (%s, %s, %s);
                    '''
            
            imgUrl = Config.S3_LOCATION + new_file_name

            record = (user_id, imgUrl, content)

            cursor = connection.cursor()
            cursor.execute(query, record)

            posting_id = cursor.lastrowid

            # 2. tag_name 테이블 처리를 해준다.
            # rekognition을 이용해서 받아온 label이 tag_name 테이블에
            # 이미 존재하면 그 아이디만 가져오고, 존재하지 않으면
            # 테이블에 insert 한 후에 그 아이디를 가져온다.

            for tag in tag_list :
                tag = tag.lower() # 소문자로 변환
                query = '''
                        select *
                        from tag_name
                        where name = %s;
                        '''
                record = (tag, )

                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, record)

                result_list = cursor.fetchall()

                # 태그가 이미 테이블에 있으면 아이디만 가져온다.
                if len(result_list) != 0 :
                    tag_name_id = result_list[0]["id"]
                else :
                    # 없다면 테이블에 insert 한 후 아이디 가져온다.
                    query = '''
                            insert into tag_name
                            (name)
                            values
                            (%s);
                            '''
                    record = (tag, )

                    cursor = connection.cursor()
                    cursor.execute(query, record)

                    tag_name_id = cursor.lastrowid

            # 3. 위 tag_name 아이디와 posting 아이디를 이용해서
            # tag 테이블에 데이터를 넣어준다.
                query = '''
                        insert into tag
                        (postingId, tagNameId)
                        values
                        (%s, %s);
                        '''
                record = (posting_id, tag_name_id)

                cursor = connection.cursor()
                cursor.execute(query, record)

            # 커밋은 테이블 처리를 다 하고나서 마지막에 한번 해준다.
            # 이렇게 해야 다른 테이블에서 문제가 발생해도 원상복구(롤백)된다.
            # 이 기능을 트랜잭션이라고 한다.
            connection.commit()

            cursor.close()
            connection.close()

        except Exception as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500

        return {"result" : "success"}, 200
    
    def detect_labels(self, photo, bucket) :

        client = boto3.client('rekognition', 'ap-northeast-2', 
                              aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)

        response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
                                        
        MaxLabels=5,
        # Uncomment to use image properties and filtration settings
        #Features=["GENERAL_LABELS", "IMAGE_PROPERTIES"],
        #Settings={"GeneralLabels": {"LabelInclusionFilters":["Cat"]},
        # "ImageProperties": {"MaxDominantColors":10}}
        )

        # print('Detected labels for ' + photo)
        # print()

        label_list = []
        for label in response['Labels']:
            # print("Label: " + label['Name'])
            # print("Confidence: " + str(label['Confidence']))

            if (label['Confidence']) >= 90 :
                label_list.append(label['Name'])

        return label_list

    # 내 친구 포스팅만 보기
    @jwt_required()
    def get(self) :

        user_id = get_jwt_identity()

        offset = request.args.get("offset")
        limit = request.args.get("limit")

        try :
            connection = get_connection()

            query = '''
                    select p.id as postId, p.imageUrl, p.content, u.id as userId, u.nickname, p.createdAt, count(fa.id) as favoriteCnt, if(fa2.id is null, 0, 1) as isFavorite
                    from follow f
                    join posting p
                    on f.followeeId = p.userId
                    join user u
                    on p.userId = u.id
                    left join favorite fa
                    on p.id = fa.postingId
                    left join favorite fa2
                    on p.id = fa2.postingId and fa2.userId = %s  
                    where f.followerId = %s
                    group by p.id
                    order by p.createdAt desc
                    limit ''' + offset + ''', ''' + limit + ''';
                    '''
            
            record = (user_id, user_id)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            i = 0
            for row in result_list :
                result_list[i]["createdAt"] = row["createdAt"].isoformat()
                i = i+1

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"result" : "fail", "error" : str(e)}, 500

        if len(result_list) == 0 :
            return {"error" : "팔로잉한 회원이 없거나 글이 없습니다."}, 400

        return {"result" : "success", "items" : result_list, "count" : len(result_list)}, 200

# 포스팅 상세 보기(태그까지)
class PostingResource(Resource) :
    @jwt_required()
    def get(self, postId) :

        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''
                    select p.id as postId, p.imageUrl, p.content, p.userId, u.nickname, p.createdAt, count(fa.id) as favoriteCnt, if(fa2.id is null, 0, 1) as isFavorite
                    from posting p
                    join user u
                    on p.userId = u.id
                    left join favorite fa
                    on p.id = fa.postingId
                    left join favorite fa2
                    on p.id = fa2.postingId and fa2.userId = %s  
                    where p.id = %s;
                    '''
            record = (user_id, postId)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            if result_list[0]["postId"] is None :
                return {"error" : "존재하지 않는 포스팅입니다."}, 400

            result_list[0]["createdAt"] = result_list[0]["createdAt"].isoformat()

            query = '''
                    select tn.name
                    from tag t
                    join tag_name tn
                    on tagNameId = tn.id
                    where t.postingId = %s;
                    '''
            record = (postId, )

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            tag_list = cursor.fetchall()

            if len(tag_list) == 0 :
                return {"error" : "해당 포스팅에 태그가 존재하지 않습니다."}, 400

            re_tag = []
            for tag in tag_list :
                re_tag.append("#" + tag["name"])

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500

        return {"result" : "success", "post" : result_list, "tag" : re_tag}, 200