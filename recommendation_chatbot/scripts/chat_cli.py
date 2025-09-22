import argparse
from core.store import load_items_from_csv
from core.taxonomy import load_major_map
from core.retrieve import merge_and_rerank
from core.llm import render_plain  # 필요시 LLM으로 바꿔도 됨

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--items_csv", required=True)
    ap.add_argument("--taxonomy_dir", default="recommendation_chatbot/data/taxonomy")
    ap.add_argument("--persist_dir", default="recommendation_chatbot/data/vector_index")
    ap.add_argument("--message", required=True, help="사용자 입력")
    args = ap.parse_args()

    items = load_items_from_csv(args.items_csv)
    tax = load_major_map(args.taxonomy_dir)
    hits = merge_and_rerank(args.message, items, tax, args.persist_dir, top_k=5)
    print(render_plain(args.message, hits))
