from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from .models import LectureReview, ActivityChatHistory, LectureChatHistory
from .login import RegisterSerializer, ActivityChatHistorySerializer, LectureChatHistorySerializer
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response


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
    



# 공모전/대회 챗봇 히스토리 API 뷰
#@method_decorator(csrf_exempt, name='dispatch')
class ActivityChatHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated] # 토큰 인증

    def get(self, request):
        # 데이터베이스에서 현재 사용자의 기록만 필터링해서 가져오기
        histories = ActivityChatHistory.objects.filter(user=request.user)
        # 시리얼라이저를 통해 데이터를 JSON으로 변환
        serializer = ActivityChatHistorySerializer(histories, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # 클라이언트가 보낸 데이터를 시리얼라이저로 검증
        serializer = ActivityChatHistorySerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user) # 현재 user정보와 함께 저장
            return Response(serializer.data, status=status.HTTP_201_CREATED)


# 강의 추천 챗봇 히스토리 API 뷰
#@method_decorator(csrf_exempt, name='dispatch')
class LectureChatHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        histories = LectureChatHistory.objects.filter(user=request.user)
        serializer = LectureChatHistorySerializer(histories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LectureChatHistorySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        



# templates 프론트 UI
from django.shortcuts import render

def main_page(request):
    return render(request, 'main/main.html')

def login_page(request):
    return render(request, 'main/login.html')

def signup_page(request):
    # 일반 회원가입
    return render(request, 'main/signup.html', context={'is_pro': False})

def signup_pro_page(request):
    # Pro 회원가입 (UI만 다르고 호출은 동일)
    return render(request, 'main/signup_pro.html', context={'is_pro': True})
