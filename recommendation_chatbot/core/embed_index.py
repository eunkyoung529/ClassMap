# 기능 : 문서 임베딩 및 Chroma 벡터 인덱스 생성/검색.
from sentence_transformers import SentenceTransformer
from chromadb import Client
from chromadb.config import Settings
from typing import List
from .store import Item

def doc_text(it: Item) -> str:
    parts = [it.title or "", it.description or "", ",".join(it.categories), ",".join(it.target_jobs), ",".join(it.target_majors)]
    return " ".join([p for p in parts if p])

def build_index(items: List[Item], persist_dir: str):
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    chroma = Client(Settings(persist_directory=persist_dir))
    # 초기화(운영에선 upsert 권장)
    try:
        col = chroma.get_or_create_collection("items")
        col.delete()
    except:
        pass
    col = chroma.get_or_create_collection("items")

    docs = [doc_text(it) for it in items]
    embs = model.encode(docs, batch_size=64, convert_to_numpy=True)
    ids = [str(it.id) for it in items]
    metas = [{"title": it.title, "host": it.host, "deadline": it.deadline, "link": it.link, "type": it.type} for it in items]

    col.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)

def vector_search(query: str, top_k: int, persist_dir: str):
    chroma = Client(Settings(persist_directory=persist_dir))
    col = chroma.get_or_create_collection("items")
    res = col.query(query_texts=[query], n_results=top_k)
    out = []
    ids = res["ids"][0]; metas = res["metadatas"][0]; dists = res["distances"][0]
    for i in range(len(ids)):
        out.append({"id": ids[i], "meta": metas[i], "score": float(dists[i])})
    return out
