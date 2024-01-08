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
                    select u.id as userId, u.nickname as userNickname, u.email as userEmail, p.id as postingId, p.imageUrl, p.content, p.createdAt,
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