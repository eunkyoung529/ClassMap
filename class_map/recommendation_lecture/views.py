
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.conf import settings


# 챗봇 핵심 로직 및 라이브러리 Import
from .retriever.data_loader import load_chunks
from .retriever.bm25 import build_bm25_index
from .chatbot.rag_chatbot import build_dense_index  # Chroma 인덱스 빌드 함수
from .retriever.hybrid import hybrid_search
from .chatbot.generator import generate_answer
from .chatbot.gpt_client import create_azure_client

from sentence_transformers import CrossEncoder

# 데이터 및 모델 사전 로드
print("="*50)
print("강의 추천 챗봇의 데이터와 모델을 로딩합니다...")

# 데이터(chunks) 로드
print(f"[1/4] 강의 데이터 로딩 중... ({settings.LECTURE_CHUNKS_PATH})")
ALL_CHUNKS = load_chunks(str(settings.LECTURE_CHUNKS_PATH))

# BM25 인덱스 빌드
print("[2/4] BM25 인덱스 빌드 중...")
BM25_INDEX, TOKENIZED_CORPUS = build_bm25_index(ALL_CHUNKS)

# ChromaDB 벡터 인덱스 빌드/로드
print(f"[3/4] ChromaDB 벡터 인덱스 로딩 중... ({settings.LECTURE_CHROMA_PATH})")
CHROMA_COLLECTION = build_dense_index(
    chunks=ALL_CHUNKS,
    persist_dir=str(settings.LECTURE_CHROMA_PATH),
    model_name=settings.EMBED_MODEL
)

# Reranker (CrossEncoder) 모델 로드
print(f"[4/4] Reranker 모델 로딩 중... ({settings.RERANK_MODEL})")
CROSS_ENCODER = CrossEncoder(settings.RERANK_MODEL)

print("강의 추천 챗봇 준비 완료.")
print("="*50)

# API 뷰 함수 정의
@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        if not user_message:
            return JsonResponse({'error': 'message field is required'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    try:
        # 챗봇 파이프라인 실행 
        print(f"사용자 질문 수신: {user_message}")

        # 사용자 질문에서 간단한 필터 자동 추출 (rag_chatbot.py 로직 참고)
        filters = {}
        for year in ["1학년", "2학년", "3학년", "4학년"]:
            if year in user_message:
                filters["target"] = year
        if "전공" in user_message:
            filters["course_type"] = "전공"
        elif "교양" in user_message or "교필" in user_message:
            filters["course_type"] = "교양"

        # Hybrid Search 실행
        hits = hybrid_search(
            chunks=ALL_CHUNKS,
            collection=CHROMA_COLLECTION,
            bm25=BM25_INDEX,
            tokenized_corpus=TOKENIZED_CORPUS,
            query=user_message,
            cross_encoder=CROSS_ENCODER,
            top_k=5,
            filters=filters
        )

        # LLM에 넘겨줄 최종 컨텍스트 선택 (부모 청크 위주)
        parent_hits = [h for h in hits if h.get("chunk_type") == "parent"]
        if not parent_hits: # 부모 청크가 없으면 그냥 chunk 사용
            parent_hits = hits

        # Azure GPT 클라이언트 생성 및 답변 생성
        client = create_azure_client()
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT") # .env 파일에 정의
        final_answer = generate_answer(user_message, parent_hits, deployment_name, client)
        # print(repr(final_answer))
        final_answer = final_answer.replace('\n', '<br>')
        return JsonResponse({'response': final_answer})


    except Exception as e:
        import traceback
        print(f"강의 추천 챗봇 처리 중 에러 발생: {e}")
        traceback.print_exc() # 터미널에 상세 에러 출력
        return JsonResponse({'error': 'An internal error occurred.'}, status=500)
    

    

# templates 프론트 UI
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie # CSRF 토큰 설정
def chatbot_page(request):
    return render(request, 'recommendation_lecuture/chatbot.html')