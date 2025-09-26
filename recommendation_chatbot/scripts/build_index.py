# from ..core.store import load_contests
# from ..core.embed_index import build_index

# def main():
#     print("[build_index] loading contests ...")
#     df = load_contests()
#     print(f"[build_index] records: {len(df)}")
#     print("[build_index] building index ...")
#     build_index(df)
#     print("[build_index] done.")

# if __name__ == "__main__":
#     main()


# -*- coding: utf-8 -*-
# 기능: items.csv를 읽어 Azure 임베딩 인덱스(JSON) 생성

import os
import argparse
from dotenv import load_dotenv; load_dotenv()
from recommendation_chatbot.core.store import load_items_from_csv
from recommendation_chatbot.core.embed_index import SimpleVectorDB

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--items_csv", default=os.getenv("ITEMS_CSV", "recommendation_chatbot/data/items.csv"))
    ap.add_argument("--persist_dir", default="recommendation_chatbot/data/vector_index")
    args = ap.parse_args()

    items = load_items_from_csv(args.items_csv)
    db = SimpleVectorDB(args.persist_dir)
    db.build(items)
    db.save()
    print("✅ 벡터 인덱스 생성 완료:", db.path)
