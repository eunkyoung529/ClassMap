from django.urls import path
from .views import chatbot_page
app_name = 'recommendation_chatbot'
urlpatterns = [
    path('', chatbot_page, name='web-chatbot'),
]
