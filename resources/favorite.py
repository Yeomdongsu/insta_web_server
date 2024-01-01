from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mysql.connector import Error
from mysql_connection import get_connection

# 좋아요
class FavoriteResource(Resource) :
    # 좋아요 추가
    @jwt_required()
    def post(self, postingId) :

        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''
                    insert into favorite
                    (userId, postingId)
                    values
                    (%s, %s);
                    '''
            
            record = (user_id, postingId)

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
    
    # 좋아요 삭제
    @jwt_required()
    def delete(self, postingId) :

        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''
                    delete from favorite
                    where userId = %s and postingId = %s;
                    '''
            
            record = (user_id, postingId)

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
    
    # 해당 글 좋아요 누른 사람 리스트
    @jwt_required()
    def get(self, postingId) :

        user_id = get_jwt_identity()

        try :
            connection = get_connection()
            
            query = '''
                    select f.userId, u.nickname  
                    from favorite f
                    left join user u
                    on f.userId = u.id
                    where f.postingId = %s;
                    '''
            record = (postingId, )

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            print(result_list)

            if len(result_list) == 0 :
                return {"error" : "해당 글에 좋아요가 없습니다."}, 400

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {"error" : str(e)}, 500
            
        return {"result" : "success", "like_list" : result_list, "count" : len(result_list)}, 200