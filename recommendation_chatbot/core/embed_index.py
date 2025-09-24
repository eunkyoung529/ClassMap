# 기능 : 문서 임베딩 및 Chroma 벡터 인덱스 생성/검색.
# from sentence_transformers import SentenceTransformer
# from chromadb import Client
# from chromadb.config import Settings
# from typing import List
# from .store import Item

# def doc_text(it: Item) -> str:
#     parts = [it.title or "", it.description or "", ",".join(it.categories), ",".join(it.target_jobs), ",".join(it.target_majors)]
#     return " ".join([p for p in parts if p])

# def build_index(items: List[Item], persist_dir: str):
#     model = SentenceTransformer("jhgan/ko-sroberta-multitask")
#     chroma = Client(Settings(persist_directory=persist_dir))
#     # 초기화(운영에선 upsert 권장)
#     try:
#         col = chroma.get_or_create_collection("items")
#         col.delete()
#     except:
#         pass
#     col = chroma.get_or_create_collection("items")

#     docs = [doc_text(it) for it in items]
#     embs = model.encode(docs, batch_size=64, convert_to_numpy=True)
#     ids = [str(it.id) for it in items]
#     metas = [{"title": it.title, "host": it.host, "deadline": it.deadline, "link": it.link, "type": it.type} for it in items]

#     col.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)

# def vector_search(query: str, top_k: int, persist_dir: str):
#     chroma = Client(Settings(persist_directory=persist_dir))
#     col = chroma.get_or_create_collection("items")
#     res = col.query(query_texts=[query], n_results=top_k)
#     out = []
#     ids = res["ids"][0]; metas = res["metadatas"][0]; dists = res["distances"][0]
#     for i in range(len(ids)):
#         out.append({"id": ids[i], "meta": metas[i], "score": float(dists[i])})
#     return out



#잘 실행되는 코드

# from __future__ import annotations
# import os
# import pickle
# from typing import Dict, Any
# import pandas as pd
# from sklearn.feature_extraction.text import TfidfVectorizer

# VECTOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vector_index")
# INDEX_PKL = os.path.join(VECTOR_DIR, "index.pkl")

# def build_index(df: pd.DataFrame) -> None:
#     os.makedirs(VECTOR_DIR, exist_ok=True)
#     vectorizer = TfidfVectorizer(
#         max_features=50000,
#         ngram_range=(1, 2),
#         min_df=1,
#     )
#     X = vectorizer.fit_transform(df["text"].tolist())
#     payload = {
#         "vectorizer": vectorizer,
#         "matrix": X,
#         "records": df[["title", "host", "deadline", "field", "link", "content", "text"]].reset_index(drop=True),
#     }
#     with open(INDEX_PKL, "wb") as f:
#         pickle.dump(payload, f)

# def load_index() -> Dict[str, Any]:
#     with open(INDEX_PKL, "rb") as f:
#         return pickle.load(f)

import os, pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from .config import VECTOR_DIR, INDEX_PKL

def build_index(df: pd.DataFrame) -> None:
    os.makedirs(VECTOR_DIR, exist_ok=True)
    vec = TfidfVectorizer(max_features=50000, ngram_range=(1,2), min_df=1)
    X = vec.fit_transform(df["text"].tolist())
    payload = {
        "vectorizer": vec,
        "matrix": X,
        "records": df[["title","host","deadline","field","link","content","text"]].reset_index(drop=True),
    }
    with open(INDEX_PKL, "wb") as f:
        pickle.dump(payload, f)

def load_index():
    with open(INDEX_PKL, "rb") as f:
        return pickle.load(f)

