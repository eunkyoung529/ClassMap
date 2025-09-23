from django.shortcuts import render
from django.http import HttpResponse

def recommendation_chatbot(request):
    return HttpResponse("This is the recommendation chatbot view.")