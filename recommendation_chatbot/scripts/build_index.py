# import argparse
# from core.store import load_items_from_csv
# from core.embed_index import build_index

# if __name__ == "__main__":
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--items_csv", required=True, help="공모전/대외활동 CSV")
#     ap.add_argument("--persist_dir", default="recommendation_chatbot/data/vector_index")
#     args = ap.parse_args()

#     items = load_items_from_csv(args.items_csv)
#     build_index(items, args.persist_dir)
#     print(f"indexed: {len(items)}")

# 잘 작동되는 코드
# from __future__ import annotations
# from tqdm import tqdm
# from ..core.store import load_contests
# from ..core.embed_index import build_index

# def main():
#     print("[build_index] loading CSV ...")
#     df = load_contests()
#     print(f"[build_index] records: {len(df)}")
#     print("[build_index] building TF-IDF index ...")
#     build_index(df)
#     print("[build_index] done.")

# if __name__ == "__main__":
#     main()

from ..core.store import load_contests
from ..core.embed_index import build_index

def main():
    print("[build_index] loading contests ...")
    df = load_contests()
    print(f"[build_index] records: {len(df)}")
    print("[build_index] building index ...")
    build_index(df)
    print("[build_index] done.")

if __name__ == "__main__":
    main()
