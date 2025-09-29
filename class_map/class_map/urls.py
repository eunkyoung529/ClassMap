"""
URL configuration for class_map project. 

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django import views
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('main.web_urls')), #웹
    path('chatbot/', include('recommendation_chatbot.web_urls')), #웹
    path('lecture/', include('recommendation_lecture.web_urls')), #웹

    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
    path('api/activities-recommendation/', include('recommendation_chatbot.urls')),
    path('api/lectures-recommendation/', include('recommendation_lecture.urls')),
]
