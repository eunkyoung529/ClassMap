from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterView, MeView
from .auth_tokens import CustomTokenObtainPairView

urlpatterns = [
    path('search/', views.LectureReviewSearchView.as_view(), name='lecture_review_search'),

    # 로그인/회원가입
    # path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    # path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('auth/me/', views.MeView.as_view(), name='auth-me'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/',    CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # 커스텀 로그인
    path('auth/refresh/',  TokenRefreshView.as_view(),          name='token_refresh'),
    path('auth/me/',       MeView.as_view(),                    name='auth-me'),
    
    # 챗봇 히스토리
    path('chat-histories/activities/', views.ActivityChatHistoryView.as_view(), name='history_activity_chat'),
    path('chat-histories/lectures/',  views.LectureChatHistoryView.as_view(),  name='history_lecture_chat'),
] 