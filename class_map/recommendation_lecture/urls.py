from django.urls import path
from . import views

urlpatterns = [
    path('', views.recommendation_lecture, name='recommendation_lecture')
]