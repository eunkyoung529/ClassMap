import argparse
from recommendation_chatbot.core.taxonomy import build_major_map

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="전국대학별학과정보표준데이터.csv 경로")
    ap.add_argument("--out", default="recommendation_chatbot/data/taxonomy", help="출력 디렉터리")
    args = ap.parse_args()
    out = build_major_map(args.src, args.out)
    print("saved:", out)
