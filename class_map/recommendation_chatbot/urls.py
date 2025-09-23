from django.urls import path
from . import views

urlpatterns = [
    path('', views.recommendation_chatbot, name='recommendation_chatbot')
]