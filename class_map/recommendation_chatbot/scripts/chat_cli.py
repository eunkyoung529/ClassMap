# -*- coding: utf-8 -*-
# 전공/진로 기반 공모전·대외활동 추천 CLI (Silent ver., no generate_major_keywords)
# 출력은 최종 추천 목록만. 중간 로그/경고 출력 없음.

from __future__ import annotations
import os
import argparse
from dotenv import load_dotenv

# 불필요한 로그 억제
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# .env 로드
load_dotenv(dotenv_path=".env")

from recommendation_chatbot.core.store import load_items_from_csv
from recommendation_chatbot.core.majors import (
    build_major_map, load_major_map, resolve_major
)
from recommendation_chatbot.core.retrieve import hybrid_search
from recommendation_chatbot.core.llm_azure import (
    render_with_llm, render_plain  # ⬅ generate_major_keywords 제거
)
from recommendation_chatbot.core.bm25_index import BM25Index
from recommendation_chatbot.core.chroma_index import ChromaIndex
from recommendation_chatbot.core.rerank import llm_rerank

TAX_DIR = "recommendation_chatbot/data/taxonomy"
VEC_DIR = "recommendation_chatbot/data/vector_index"

def ensure_major_map(path_csv: str):
    os.makedirs(TAX_DIR, exist_ok=True)
    out = os.path.join(TAX_DIR, "majors_jobs_map.json")
    if not os.path.exists(out):
        try:
            build_major_map(path_csv, TAX_DIR)
        except Exception:
            pass

def has_azure_chat() -> bool:
    need = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_CHAT_DEPLOYMENT"]
    return all(os.getenv(k) for k in need)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="전공/진로 기반 공모전·대외활동 추천 CLI (silent)")
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

    # 데이터/전공 맵
    ensure_major_map(args.majors_csv)
    try:
        tax = load_major_map(TAX_DIR)
    except Exception:
        tax = {}
    try:
        items = load_items_from_csv(args.items_csv)
    except Exception:
        items = []

    # 인덱스
    bm25 = BM25Index(items) if items else None
    chroma = None
    try:
        chroma = ChromaIndex(args.persist_dir)
        try:
            if not chroma.col.count():
                chroma.build(items)
        except Exception:
            chroma.build(items)
    except Exception:
        chroma = None

    # 전공/직업 키워드
    major, jobs = resolve_major(args.message, tax)

    if bm25 is None:
        ranked, famous, prefs = [], None, []
    else:
        ranked, famous, prefs = hybrid_search(
            user_text=args.message,
            items=items,
            major=major,
            major_jobs=jobs or [],   # 비어 있으면 빈 리스트
            bm25=bm25,
            chroma=chroma,
            top_k=10,
            w_bm25=args.w_bm25,
            w_chroma=args.w_chroma
        )

    use_llm_rerank = (not args.no_llm_rerank) and has_azure_chat()
    if use_llm_rerank and ranked:
        try:
            ranked = llm_rerank(args.message, ranked, top_k=10)
        except Exception:
            ranked = ranked[:10]
    else:
        ranked = ranked[:10]

    use_llm_summary = (not args.no_llm_summary) and has_azure_chat()
    if use_llm_summary:
        try:
            output = render_with_llm(args.user, args.message, ranked, famous, prefs, hide_deadline=True)
        except Exception:
            output = render_plain(args.user, args.message, ranked, famous, prefs, hide_deadline=True)
    else:
        output = render_plain(args.user, args.message, ranked, famous, prefs, hide_deadline=True)

    # 최종 출력만
    print(output)
