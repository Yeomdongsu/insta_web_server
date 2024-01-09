from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from mysql.connector import Error
from mysql_connection import get_connection

class FollowResource(Resource) :
    # 친구 맺기
    @jwt_required()
    def post(self, followee_id) :

        user_id = get_jwt_identity()

        if followee_id == user_id :
            return {"error" : "자기 자신과는 친구할 수 없습니다."}, 400
        
        try :
            connection = get_connection()

            query = '''
                    insert into follow
                    (followerId, followeeId)
                    values
                    (%s, %s);
                    '''
            record = (user_id, followee_id)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"result" : "fail", "error" : str(e)}, 500

        return {"result" : "success"}, 200
    
    # 친구 끊기
    @jwt_required()
    def delete(self, followee_id) :
        
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query ='''
                    delete from follow
                    where followerId = %s and followeeId = %s;
                    '''
            record = (user_id, followee_id)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"result" : "fail", "error" : str(e)}, 500
        
        return {"result" : "success"}, 200

class FollowerListResource(Resource) :
    # 나를 팔로우 하는 리스트
    @jwt_required()
    def get(self) :
        
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''
                    select u.id, u.nickname, if(f2.id is null, 0, 1) as isFollow
                    from user u
                    left join follow f
                    on f.followerId = u.id
                    left join follow f2
                    on f2.followeeId = u.id and f2.followerId = %s
                    where f.followeeId = %s;
                    '''
            record = (user_id, user_id)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500

        return {"result" : "success", "followers" : result_list}, 200
    
class FollowingListResource(Resource) :
    # 내가 팔로잉 하는 리스트
    @jwt_required()
    def get(self) :

        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''
                    select u.id, u.nickname, if(f2.id is null, 0, 1) as isFollow
                    from user u
                    left join follow f
                    on u.id = f.followeeId
                    left join follow f2
                    on u.id = f2.followerId and f2.followeeId = %s
                    where f.followerId = %s;
                    '''
            record = (user_id, user_id)
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500

        return {"result" : "success", "following" : result_list}, 200