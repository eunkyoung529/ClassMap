# import argparse
# from ..core.config import TOP_K
# from ..core.embed_index import load_index  # 존재 확인
# from ..core.majors import expand_query_with_major
# from ..core.retrieve import search_with_profile
# from ..core.llm import generate_answer

# BANNER = "공모전/대외활동 추천 챗봇 (LLM + RAG)"
# PROMPT = "YOU> "

# def main():
#     parser = argparse.ArgumentParser(description=BANNER)
#     parser.add_argument("--name", default="사용자")
#     parser.add_argument("--major", default="컴퓨터공학과")
#     args = parser.parse_args()

#     _ = load_index()

#     print(BANNER)
#     print("예시: 나는 건축학과인데 BIM/친환경 공모전 추천해줘")
#     print("종료: Ctrl+C\n")

#     user_name = args.name
#     user_major = args.major

#     while True:
#         try:
#             utter = input(PROMPT).strip()
#             if not utter:
#                 continue
#             if ("학과" in utter) or ("전공" in utter):
#                 user_major = utter

#             # 전공+관심 강화 검색
#             recs = search_with_profile(user_major, utter, top_k=TOP_K)
#             answer = generate_answer(user_name, user_major, utter, recs)
#             print("\n" + answer + "\n")
#         except KeyboardInterrupt:
#             print("\n종료합니다.")
#             break

# if __name__ == "__main__":
#     main()



# 임베딩 있는 버전
# -*- coding: utf-8 -*-
# 기능: 로컬 CLI에서 추천 챗 확인
# import os, argparse
# from dotenv import load_dotenv; load_dotenv()
# from recommendation_chatbot.core.store import load_items_from_csv
# from recommendation_chatbot.core.embed_index import SimpleVectorDB
# from recommendation_chatbot.core.majors import build_major_map, load_major_map, resolve_major
# from recommendation_chatbot.core.retrieve import hybrid_search
# from recommendation_chatbot.core.llm_azure import render_with_llm, render_plain, generate_major_keywords

# TAX_DIR = "recommendation_chatbot/data/taxonomy"
# VEC_DIR = "recommendation_chatbot/data/vector_index"

# def ensure_major_map(path_csv: str):
#     os.makedirs(TAX_DIR, exist_ok=True)
#     out = os.path.join(TAX_DIR, "majors_jobs_map.json")
#     if not os.path.exists(out):
#         print("ℹ️ 전공 맵이 없어서 생성합니다...")
#         build_major_map(path_csv, TAX_DIR)

# if __name__ == "__main__":
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--user", default="사용자")
#     ap.add_argument("--message", required=True)
#     ap.add_argument("--items_csv", default=os.getenv("ITEMS_CSV", "recommendation_chatbot/data/items.csv"))
#     ap.add_argument("--majors_csv", default=os.getenv("MAJORS_CSV", "전국대학별학과정보표준데이터.csv"))
#     ap.add_argument("--persist_dir", default=VEC_DIR)
#     ap.add_argument("--no_llm", action="store_true")
#     args = ap.parse_args()

#     # 1) 데이터 준비
#     ensure_major_map(args.majors_csv)
#     tax = load_major_map(TAX_DIR)
#     items = load_items_from_csv(args.items_csv)

#     # 2) 벡터 인덱스 로드(없으면 즉석 빌드)
#     db = SimpleVectorDB(args.persist_dir)
#     try:
#         db.load()
#     except FileNotFoundError:
#         print("ℹ️ 벡터 인덱스가 없어 즉시 빌드합니다...")
#         db.build(items)
#         db.save()

#     # 3) 전공 해석
#     major, jobs = resolve_major(args.message, tax)
#     if major and not jobs:
#         # 표준데이터에 직업이 비어있을 때 LLM 보강
#         jobs = generate_major_keywords(major.name, fallback=[])

#     # 4) 검색/리랭크
#     ranked, famous, prefs = hybrid_search(args.message, items, major, jobs, db, top_k=10)

#     # 5) 렌더
#     if args.no_llm:
#         print("\n" + render_plain(args.user, args.message, ranked, famous, prefs))
#     else:
#         print("\n" + render_with_llm(args.user, args.message, ranked, famous, prefs))






# -*- coding: utf-8 -*-
# 기능: 전공/진로 기반 공모전·대외활동 추천 CLI (BM25 + Chroma + LLM rerank)
# 사용 예:
#   python -m recommendation_chatbot.scripts.chat_cli --message "건축학과 설계 공모전 추천"
#   python -m recommendation_chatbot.scripts.chat_cli --message "심리학과 임상/연구 포스터 추천"
#   python -m recommendation_chatbot.scripts.chat_cli --message "영어영문학과 영문 에세이/번역 공모전 추천"
#   python -m recommendation_chatbot.scripts.chat_cli --message "법학과 모의법정/토론 대회 추천"

# from __future__ import annotations
# import os
# import argparse
# from dotenv import load_dotenv

# # 루트의 .env 로드 (어디서 실행해도 동일하게)
# load_dotenv(dotenv_path=".env")

# from recommendation_chatbot.core.store import load_items_from_csv
# from recommendation_chatbot.core.majors import (
#     build_major_map, load_major_map, resolve_major
# )
# from recommendation_chatbot.core.retrieve import hybrid_search
# from recommendation_chatbot.core.llm_azure import (
#     render_with_llm, render_plain, generate_major_keywords
# )

# # 새로 추가된 모듈들
# from recommendation_chatbot.core.bm25_index import BM25Index
# from recommendation_chatbot.core.chroma_index import ChromaIndex
# from recommendation_chatbot.core.rerank import llm_rerank

# TAX_DIR = "recommendation_chatbot/data/taxonomy"
# VEC_DIR = "recommendation_chatbot/data/vector_index"

# def ensure_major_map(path_csv: str):
#     """전공 맵(json)이 없으면 표준데이터 CSV로부터 생성"""
#     os.makedirs(TAX_DIR, exist_ok=True)
#     out = os.path.join(TAX_DIR, "majors_jobs_map.json")
#     if not os.path.exists(out):
#         print("ℹ️ 전공 맵이 없어 생성합니다...")
#         build_major_map(path_csv, TAX_DIR)

# def has_azure_chat() -> bool:
#     """LLM(요약/리랭크) 가능 여부"""
#     need = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_CHAT_DEPLOYMENT"]
#     return all(os.getenv(k) for k in need)

# if __name__ == "__main__":
#     ap = argparse.ArgumentParser(description="전공/진로 기반 공모전·대외활동 추천 CLI")
#     ap.add_argument("--user", default="사용자", help="사용자 표시 이름")
#     ap.add_argument("--message", required=True, help="사용자 요청 문장")
#     ap.add_argument("--items_csv", default=os.getenv("ITEMS_CSV", "recommendation_chatbot/data/items.csv"),
#                     help="공모전/대외활동 CSV 경로")
#     ap.add_argument("--majors_csv", default=os.getenv("MAJORS_CSV", "전국대학별학과정보표준데이터.csv"),
#                     help="전국대학별학과정보표준데이터 CSV 경로")
#     ap.add_argument("--persist_dir", default=VEC_DIR, help="인덱스/벡터 저장 폴더(Chroma가 사용)")
#     ap.add_argument("--no_llm_summary", action="store_true", help="LLM 요약 비활성화(plain 출력)")
#     ap.add_argument("--no_llm_rerank", action="store_true", help="LLM 리랭킹 비활성화")
#     ap.add_argument("--w_bm25", type=float, default=0.7, help="BM25 키워드 가중치(기본 0.7)")
#     ap.add_argument("--w_chroma", type=float, default=0.3, help="Chroma 의미 가중치(기본 0.3)")
#     args = ap.parse_args()

#     # 1) 데이터 준비
#     ensure_major_map(args.majors_csv)
#     tax = load_major_map(TAX_DIR)
#     items = load_items_from_csv(args.items_csv)

#     # 2) 인덱스 준비
#     # BM25: 메모리 기반, 항상 사용
#     bm25 = BM25Index(items)

#     # Chroma: 로컬 임베딩(문장변환기)으로 의미검색, Azure 임베딩 불필요
#     chroma = None
#     try:
#         chroma = ChromaIndex(args.persist_dir)  # persist_dir: recommendation_chatbot/data/vector_index
#         # 컬렉션이 비어 있으면 최초 구축
#         try:
#             need_build = (chroma.col.count() == 0)
#         except Exception:
#             need_build = True
#         if need_build:
#             print("ℹ️ Chroma 컬렉션이 비어 있어 구축합니다(최초 1회, 로컬 임베딩).")
#             chroma.build(items)
#     except Exception as e:
#         print(f"⚠️ Chroma 초기화 실패로 의미검색(로컬) 비활성화: {e}")
#         chroma = None

#     # 3) 전공 해석 (표준데이터 기반 + 근사 매칭)
#     major, jobs = resolve_major(args.message, tax)
#     if major and not jobs:
#         # 표준데이터에 관련직업명이 비었을 때 LLM로 보강(키 없으면 내부 폴백)
#         jobs = generate_major_keywords(major.name, fallback=[])

#     # 4) 하이브리드 검색 (BM25 + Chroma, 키워드 가중치↑)
#     ranked, famous, prefs = hybrid_search(
#         user_text=args.message,
#         items=items,
#         major=major,
#         major_jobs=jobs,
#         bm25=bm25,
#         chroma=chroma,
#         top_k=20,                    # LLM 리랭크 전에 넉넉히 뽑기
#         w_bm25=args.w_bm25,
#         w_chroma=args.w_chroma
#     )

#     # 5) LLM 리랭크 (임베딩 필요 없음 / Chat 배포만 필요)
#     use_llm_rerank = (not args.no_llm_rerank) and has_azure_chat()
#     if use_llm_rerank:
#         try:
#             ranked = llm_rerank(args.message, ranked, top_k=10)
#         except Exception as e:
#             print(f"⚠️ LLM 리랭크 실패(원인: {e}) — 기본 랭킹 사용")
#             ranked = ranked[:10]
#     else:
#         if not has_azure_chat() and not args.no_llm_rerank:
#             print("⚠️ Chat 배포 없음: LLM 리랭킹 없이 기본 랭킹을 사용합니다.")
#         ranked = ranked[:10]

#     # 6) 응답 렌더(요약은 선택)
#     use_llm_summary = (not args.no_llm_summary) and has_azure_chat()
#     if use_llm_summary:
#         output = render_with_llm(args.user, args.message, ranked, famous, prefs)
#     else:
#         if not has_azure_chat() and not args.no_llm_summary:
#             print("⚠️ Chat 배포 없음: LLM 요약 없이 plain 텍스트로 출력합니다.")
#         elif args.no_llm_summary:
#             print("ℹ️ --no_llm_summary 옵션으로 LLM 요약을 비활성화했습니다.")
#         output = render_plain(args.user, args.message, ranked, famous, prefs)

#     print("\n" + output)



# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import argparse
from dotenv import load_dotenv

# 로그 억제(선택)
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

load_dotenv(dotenv_path=".env")

from recommendation_chatbot.core.store import load_items_from_csv
from recommendation_chatbot.core.majors import build_major_map, load_major_map, resolve_major
from recommendation_chatbot.core.retrieve import hybrid_search
from recommendation_chatbot.core.llm_azure import render_with_llm, render_plain
from recommendation_chatbot.core.bm25_index import BM25Index
from recommendation_chatbot.core.chroma_index import ChromaIndex
from recommendation_chatbot.core.rerank import llm_rerank

TAX_DIR = "recommendation_chatbot/data/taxonomy"
VEC_DIR = "recommendation_chatbot/data/vector_index"

def ensure_major_map(path_csv: str):
    os.makedirs(TAX_DIR, exist_ok=True)
    out = os.path.join(TAX_DIR, "majors_jobs_map.json")
    if not os.path.exists(out):
        print("ℹ️ 전공 맵이 없어 생성합니다...")
        build_major_map(path_csv, TAX_DIR)

def has_azure_chat() -> bool:
    need = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_CHAT_DEPLOYMENT"]
    return all(os.getenv(k) for k in need)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="전공/진로 기반 공모전·대외활동 추천 CLI")
    ap.add_argument("--user", default="사용자")
    ap.add_argument("--message", required=True)
    ap.add_argument("--items_csv", default=os.getenv("ITEMS_CSV", "recommendation_chatbot/data/items.csv"))
    ap.add_argument("--majors_csv", default=os.getenv("MAJORS_CSV", "전국대학별학과정보표준데이터.csv"))
    ap.add_argument("--persist_dir", default=VEC_DIR)
    ap.add_argument("--no_llm_summary", action="store_true")
    ap.add_argument("--no_llm_rerank", action="store_true")
    ap.add_argument("--w_bm25", type=float, default=0.85)
    ap.add_argument("--w_chroma", type=float, default=0.15)
    args = ap.parse_args()

    ensure_major_map(args.majors_csv)
    tax = load_major_map(TAX_DIR)
    items = load_items_from_csv(args.items_csv)

    bm25 = BM25Index(items)
    chroma = None
    try:
        chroma = ChromaIndex(args.persist_dir)
        try:
            if not chroma.col.count():
                print("ℹ️ Chroma 컬렉션이 비어 있어 구축합니다(최초 1회, 로컬 임베딩).")
                chroma.build(items)
        except Exception:
            print("ℹ️ Chroma 상태 확인 실패 → 재구축 시도")
            chroma.build(items)
    except Exception as e:
        print(f"⚠️ Chroma 초기화 실패로 의미검색(로컬) 비활성화: {e}")
        chroma = None

    major, jobs = resolve_major(args.message, tax)

    ranked, famous, prefs = hybrid_search(
        user_text=args.message,
        items=items,
        major=major,
        major_jobs=jobs,
        bm25=bm25,
        chroma=chroma,
        top_k=10,                 # ✅ 항상 10개
        w_bm25=args.w_bm25,
        w_chroma=args.w_chroma
    )

    use_llm_rerank = (not args.no_llm_rerank) and has_azure_chat()
    if use_llm_rerank:
        try:
            ranked = llm_rerank(args.message, ranked, top_k=10)
        except Exception as e:
            print(f"⚠️ LLM 리랭크 실패(원인: {e}) — 기본 랭킹 사용")
            ranked = ranked[:10]
    else:
        if not has_azure_chat() and not args.no_llm_rerank:
            print("⚠️ Chat 배포 없음: LLM 리랭킹 없이 기본 랭킹을 사용합니다.")
        ranked = ranked[:10]

    # ✅ 출력에서 '마감일' 제거하도록 plain 렌더 호출(LLM 요약도 마감일 제외 안내)
    use_llm_summary = (not args.no_llm_summary) and has_azure_chat()
    if use_llm_summary:
        output = render_with_llm(args.user, args.message, ranked, famous, prefs, hide_deadline=True)
    else:
        if not has_azure_chat() and not args.no_llm_summary:
            print("⚠️ Chat 배포 없음: LLM 요약 없이 plain 텍스트로 출력합니다.")
        output = render_plain(args.user, args.message, ranked, famous, prefs, hide_deadline=True)

    print("\n" + output)
