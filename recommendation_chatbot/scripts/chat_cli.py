# import argparse
# from core.store import load_items_from_csv
# from core.taxonomy import load_major_map
# from core.retrieve import merge_and_rerank
# from core.llm import render_plain  # 필요시 LLM으로 바꿔도 됨

# if __name__ == "__main__":
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--items_csv", required=True)
#     ap.add_argument("--taxonomy_dir", default="recommendation_chatbot/data/taxonomy")
#     ap.add_argument("--persist_dir", default="recommendation_chatbot/data/vector_index")
#     ap.add_argument("--message", required=True, help="사용자 입력")
#     args = ap.parse_args()

#     items = load_items_from_csv(args.items_csv)
#     tax = load_major_map(args.taxonomy_dir)
#     hits = merge_and_rerank(args.message, items, tax, args.persist_dir, top_k=5)
#     print(render_plain(args.message, hits))

# Azure 추가 한 코드

# import argparse
# from core.store import load_items_from_csv, merge_ratings
# from core.taxonomy import load_major_map
# from core.retrieve import merge_and_rerank
# from core.llm_azure import render_azure  # (또는 llm_vertex.render_vertex)

# if __name__ == "__main__":
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--items_csv", required=True)
#     ap.add_argument("--message", required=True)
#     ap.add_argument("--user_name", default="사용자")
#     ap.add_argument("--taxonomy_dir", default="recommendation_chatbot/data/taxonomy")
#     ap.add_argument("--ratings_csv", default="recommendation_chatbot/data/ratings.csv")
#     ap.add_argument("--persist_dir", default="recommendation_chatbot/data/vector_index")
#     ap.add_argument("--provider", choices=["azure","vertex"], default="azure")
#     args = ap.parse_args()

#     items = load_items_from_csv(args.items_csv)
#     merge_ratings(items, args.ratings_csv)
#     tax = load_major_map(args.taxonomy_dir)

#     ranked, famous, prefs = merge_and_rerank(args.message, items, tax, args.persist_dir, top_k=5)

#     if args.provider == "azure":
#         out = render_azure(args.user_name, args.message, ranked, famous, prefs)
#     else:
#         from core.llm_vertex import render_vertex
#         out = render_vertex(args.user_name, args.message, ranked, famous, prefs)

#     print(out)


# 컴공만 추천됨
# from __future__ import annotations
# import argparse
# from ..core.embed_index import load_index  # 인덱스 존재 확인 용
# from ..core.retrieve import search
# from ..core.llm import format_reply
# from ..core.taxonomy import expand_query_with_major

# BANNER = "공모전/대외활동 추천 챗봇 (터미널)"
# PROMPT = "YOU> "

# def main():
#     parser = argparse.ArgumentParser(description=BANNER)
#     parser.add_argument("--name", default="사용자")
#     parser.add_argument("--major", default="컴퓨터공학과")
#     args = parser.parse_args()

#     # 인덱스 로딩 확인 (미존재시 에러 유도)
#     _ = load_index()

#     print(BANNER)
#     print("예시: 나는 컴퓨터공학과인데 개발과 관련된 공모전/대외활동 추천해줘")
#     print("종료: Ctrl+C")
#     print()

#     user_name = args.name
#     user_major = args.major

#     while True:
#         try:
#             utter = input(PROMPT).strip()
#             if not utter:
#                 continue

#             if ("학과" in utter) or ("전공" in utter):
#                 user_major = utter

#             q = expand_query_with_major(user_major, utter)
#             recs = search(q, top_k=6)
#             print()
#             print(format_reply(user_name, user_major, recs))
#             print()
#         except KeyboardInterrupt:
#             print("\n종료합니다.")
#             break

# if __name__ == "__main__":
#     main()

import argparse
from ..core.config import TOP_K
from ..core.embed_index import load_index  # 존재 확인
from ..core.majors import expand_query_with_major
from ..core.retrieve import search_with_profile
from ..core.llm import generate_answer

BANNER = "공모전/대외활동 추천 챗봇 (LLM + RAG)"
PROMPT = "YOU> "

def main():
    parser = argparse.ArgumentParser(description=BANNER)
    parser.add_argument("--name", default="사용자")
    parser.add_argument("--major", default="컴퓨터공학과")
    args = parser.parse_args()

    _ = load_index()

    print(BANNER)
    print("예시: 나는 건축학과인데 BIM/친환경 공모전 추천해줘")
    print("종료: Ctrl+C\n")

    user_name = args.name
    user_major = args.major

    while True:
        try:
            utter = input(PROMPT).strip()
            if not utter:
                continue
            if ("학과" in utter) or ("전공" in utter):
                user_major = utter

            # 전공+관심 강화 검색
            recs = search_with_profile(user_major, utter, top_k=TOP_K)
            answer = generate_answer(user_name, user_major, utter, recs)
            print("\n" + answer + "\n")
        except KeyboardInterrupt:
            print("\n종료합니다.")
            break

if __name__ == "__main__":
    main()

