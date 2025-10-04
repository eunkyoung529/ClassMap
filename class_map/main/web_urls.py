from django.urls import path
from .views import main_page, login_page, signup_page, signup_pro_page, search_page

urlpatterns = [
    path('', main_page, name='web-main'),
    path('login/', login_page, name='web-login'),
    path('signup/', signup_page, name='web-signup'),
    path('signup/pro/', signup_pro_page, name='web-signup-pro'),
    path('search/', search_page, name='search')
]
