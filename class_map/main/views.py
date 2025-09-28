from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from .models import LectureReview
from .login import RegisterSerializer
from django.contrib.auth.models import User
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response




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


#로그인/회원가입


from .login import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    body 예시:
    {
      "username": "eunki",            # 아이디
      "name": "김은경",               # 이름(표시용)
      "password": "StrongPass123!",
      "password2": "StrongPass123!",
      "paid_amount": 10000            # 10000 이상이면 pro, 미입력/미만이면 free
    }
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """
    GET /api/auth/me/    (Authorization: Bearer <access>)
    로그인 사용자 정보 + 등급 조회
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        u = request.user
        p = getattr(u, "profile", None)
        return Response({
            "id": u.id,
            "username": u.username,
            "name": u.first_name,
            "email": u.email,
            "plan": getattr(p, "plan", "free"),
            "pro_badge": getattr(p, "has_pro_badge", False),
        })