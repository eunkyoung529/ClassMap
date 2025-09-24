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

