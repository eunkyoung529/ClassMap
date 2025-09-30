from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings


# 챗폿 core 로직 import 
from .core.retrieve import hybrid_search 
from .core.llm_azure import render_with_llm 
from .core.store import Item, load_items_from_csv
from .core.majors import load_major_map, resolve_major
from .core.bm25_index import BM25Index
from .core.chroma_index import ChromaIndex

# 데이터 및 모델 사전 import 
print("데이터와 모델을 로딩합니다...")
ALL_ITEMS = load_items_from_csv(settings.ITEMS_CSV_PATH)
ALL_MAJORS = load_major_map(settings.MAJORS_DATA_DIR) 
BM25_INDEX = BM25Index(ALL_ITEMS) # 키워드 기반 검색 인덱스 생성
CHROMA_INDEX = None # 의미 기반 검색 인덱스 초기화
try:
    CHROMA_INDEX = ChromaIndex(settings.CHROMA_INDEX_PATH)
except Exception as e:
    print(f"Chroma 인덱스 로딩 실패: {e}")

print("데이터 및 모델 로딩 완료.")

# API 뷰 함수 정의
@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        # 클라이언트로부터 받은 JSON 데이터 파싱
        data = json.loads(request.body)
        user_message = data.get('message')
        user_name = data.get('user', '사용자') # 'user' 필드가 없으면 기본값 사용

        if not user_message:
            return JsonResponse({'error': 'message field is required'}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    # 챗봇 파이프라인 실행
    try:
        # 전공 정보 처리
        major_entry, major_jobs = resolve_major(user_message, ALL_MAJORS)
        
        # Retrieve: hybrid_search 함수 호출하여 관련 아이템 검색
        ranked_items, famous_item, preferences = hybrid_search(
            user_text=user_message,
            items=ALL_ITEMS,
            major=major_entry,
            major_jobs=major_jobs,
            bm25=BM25_INDEX,
            chroma=CHROMA_INDEX
        )

        # Render (LLM): llm_azure.py의 함수를 호출하여 최종 답변 생성
        final_response = render_with_llm(
            user=user_name,
            query=user_message,
            items=ranked_items,
            famous=famous_item,
            prefs=preferences
        )

        return JsonResponse({'response': final_response})

    except Exception as e:
        print(f"챗봇 처리 중 에러 발생: {e}")
        return JsonResponse({'error': 'An internal error occurred.'}, status=500)



# templates 프론트 UI
from django.shortcuts import render

from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie # CSRF 토큰 설정
def chatbot_page(request):
    return render(request, 'recommendation_chatbot/chatbot.html')