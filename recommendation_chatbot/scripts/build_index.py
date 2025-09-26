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
    print("벡터 인덱스 생성 완료:", db.path)
