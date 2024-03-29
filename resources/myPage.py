from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mysql.connector import Error
from mysql_connection import get_connection

class myPageResource(Resource) :

    # 마이페이지
    @jwt_required()
    def get(self, userId) :
        
        try :
            connection = get_connection()

            query = '''
                    select u.id as userId, u.nickname as userNickname, u.email as userEmail, ifnull(p.id, -1) as postingId, ifnull(p.imageUrl, null) as imageUrl, ifnull(p.content, null) as content, ifnull(p.createdAt, null) as createdAt,
                    count(p.id) over () as postingCnt, count(distinct f1.id) as followingCnt, count(distinct f2.id) as followersCnt
                    from user u
                    left join posting p
                    on u.id = p.userId
                    left join follow f1
                    on u.id = f1.followerId
                    left join follow f2
                    on u.id = f2.followeeId
                    where u.id = %s
                    group by u.id, p.id
                    order by p.createdAt desc;
                    '''
            
            record = (userId, )

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            if len(result_list) == 0 :
                return {"error" : "존재하지 않는 유저입니다."}, 400
            
            if (result_list[0]["postingId"] > 0) :
                i = 0
                for row in result_list :
                    result_list[i]["createdAt"] = row["createdAt"].isoformat()
                    i = i+1

            connection.close()
            cursor.close()

        except Error as e :
            print(e)
            connection.close()
            cursor.close()
            return {"error" : str(e)}, 500

        return {"result" : "success", "items" : result_list, "count" : len(result_list)}, 200
    
    # 내 정보 수정(닉네임만)
    @jwt_required()
    def post(self, userId) : 

        updateNickname = request.get_json()
        
        try :
            connection = get_connection()

            query = '''
                    update user
                    set nickname = %s
                    where id = %s;
                    '''
            
            record = (updateNickname["nickname"], userId)
            cursor = connection.cursor()
            cursor.execute(query, record)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
        
        return {"result" : "success"}, 200
