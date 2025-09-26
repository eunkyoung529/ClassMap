from django.shortcuts import render
from django.http import HttpResponse

def recommendation_lecture(request):
    return HttpResponse("This is the recommendation lecture view.")