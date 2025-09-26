from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from .models import LectureReview


def index(request):
    return HttpResponse("This is the main index view.")

# 에타 수강평 csv 검색 기능
def search_reviews(request):
    q = (request.GET.get('q', '')).strip() # 쿼리 파라미터에서 검색어 추출 및 공백 제거
    if not q: # 빈 검색어 처리
        return JsonResponse({"results": []}, status=400)
    
    # 제목에 검색어가 포함된 수강평 조회
    qs = (LectureReview.objects 
          .filter(title__icontains=q)
          .values("title", "professor", "semester", "content"))

    return JsonResponse(
        {"results": list(qs)},
        json_dumps_params={"ensure_ascii": False} # 한글 깨짐 방지
    )
