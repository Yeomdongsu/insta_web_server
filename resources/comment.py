from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mysql.connector import Error
from mysql_connection import get_connection

class CommentResource(Resource) :
    # 댓글 달기
    @jwt_required()
    def post(self, postId) :

        user_id = get_jwt_identity()
        data = request.get_json()

        try :
            connection = get_connection()

            query = '''
                    insert into comment
                    (userId, postingId, postComment)
                    values
                    (%s, %s, %s);
                    '''
            record = (user_id, postId, data["postComment"])

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
    
    # 댓글 삭제
    @jwt_required()
    def delete(self, postId) :

        user_id = get_jwt_identity()
        commentId = request.args.get("commentId")

        try :
            connection = get_connection()

            query = '''
                    delete from comment
                    where id = %s and userId = %s and postingId = %s;
                    '''
            record = (commentId, user_id, postId)

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

    # 댓글 리스트 가져오기
    @jwt_required()
    def get(self, postId) :

        try :
            connection = get_connection()

            query = '''
                    select c.id as commentId, u.id as userId, u.nickname, c.postComment as comment, c.createdAt
                    from comment c
                    left join user u
                    on c.userId = u.id
                    where c.postingId = %s
                    order by c.createdAt asc;
                    '''
            record = (postId, )
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            connection.close()
            cursor.close()

        except Error as e :
            print(e)
            connection.close()
            cursor.close()
            return {"error" : str(e)}, 500

        return {"result" : "success", "commentList" : result_list, "count" : len(result_list)}, 200