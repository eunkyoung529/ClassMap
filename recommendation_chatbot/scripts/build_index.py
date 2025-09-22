import argparse
from core.store import load_items_from_csv
from core.embed_index import build_index

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--items_csv", required=True, help="공모전/대외활동 CSV")
    ap.add_argument("--persist_dir", default="recommendation_chatbot/data/vector_index")
    args = ap.parse_args()

    items = load_items_from_csv(args.items_csv)
    build_index(items, args.persist_dir)
    print(f"indexed: {len(items)}")
