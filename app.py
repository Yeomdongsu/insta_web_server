from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from config import Config
from resources.comment import CommentDeleteResource, CommentResource
from resources.favorite import FavoriteResource
from resources.follow import FollowResource, FollowerListResource, FollowingListResource
from resources.myPage import myPageResource
from resources.posting import PostingListResource, PostingResource
from resources.user import KakaoUserRegisterResource, UserLoginResource, UserLogoutResourcce, UserRegisterResource
# 로그아웃 관련된 import문
from resources.user import jwt_blocklist

# flask 프레임워크를 이용한 Restful API 서버 개발

app = Flask(__name__)

# 환경변수 세팅
app.config.from_object(Config)
# JWT 매니저를 초기화
jwt = JWTManager(app)
# 로그아웃된 토큰으로 요청하면, 실행되지 않게 처리하는 코드
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload) :
    jti = jwt_payload['jti']
    return jti in jwt_blocklist

api = Api(app)

# API를 구분해서 실행시키는 것은 HTTP method와 url의 조합이다.

# 리소스(API코드)와 경로를 연결한다.
api.add_resource(UserRegisterResource, "/user/register") # 회원가입
api.add_resource(KakaoUserRegisterResource, "/user/kakao/register") # 카카오로 회원가입
api.add_resource(UserLoginResource, "/user/login") # 로그인
api.add_resource(UserLogoutResourcce, "/user/logout") # 로그아웃
api.add_resource(PostingListResource, "/posting") # 글쓰기 관련
api.add_resource(PostingResource, "/posting/<int:postId>") # 글 상세정보, 삭제
api.add_resource(FollowResource, "/follow/<int:followee_id>") # 팔로우
api.add_resource(FollowerListResource, "/follower/<int:userId>") # 팔로워 리스트 
api.add_resource(FollowingListResource, "/followee/<int:userId>") # 팔로잉 리스트
api.add_resource(FavoriteResource, "/favorite/<int:postingId>") # 좋아요
api.add_resource(CommentResource, "/comment/<int:postId>") # 댓글 관련
api.add_resource(CommentDeleteResource, "/comment/<int:commentId>")
api.add_resource(myPageResource, "/myPage/<int:userId>") # 마이페이지

if __name__ == "__main__" :
    app.run()