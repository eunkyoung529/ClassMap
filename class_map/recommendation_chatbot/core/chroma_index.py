from __future__ import annotations
from typing import List, Tuple, Dict
import os, hashlib
import chromadb
from chromadb import Settings
from chromadb.utils import embedding_functions
from .store import Item

def _doc_text(it: Item) -> str:
    return " ".join([
        it.title or "", it.host or "", ",".join(it.categories), it.description or ""
    ]).strip()

class ChromaIndex:
    """
    Azure 임베딩 없이, 로컬 sentence-transformers 임베딩으로 의미검색.
    persist_dir 아래에 파케(duckdb)로 영속 저장.
    """
    def __init__(self, persist_dir: str, collection: str = "items"):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=False))
        model_name = os.getenv("LOCAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
        self.col = self.client.get_or_create_collection(name=collection, embedding_function=self.embed_fn)

    def reset(self):
        self.client.reset()

    def build(self, items: List[Item]):
        try:
            self.client.delete_collection(self.col.name)
        except Exception:
            pass
        self.col = self.client.create_collection(name=self.col.name, embedding_function=self.embed_fn)

        ids, docs, metas = [], [], []
        for it in items:
            ids.append(it.id)
            docs.append(_doc_text(it))
            metas.append({
                "title": it.title, "host": it.host, "deadline": it.deadline,
                "link": it.link, "categories": ",".join(it.categories)
            })
        self.col.add(ids=ids, documents=docs, metadatas=metas)

    def search(self, query: str, top_k: int = 40) -> List[Tuple[str, float]]:
        if not query.strip():
            return []
        r = self.col.query(query_texts=[query], n_results=top_k)
        ids = r.get("ids", [[]])[0]
        dists = r.get("distances", [[]])[0] 
        out = []
        for _id, dist in zip(ids, dists):
            if _id:
                out.append((_id, float(dist)))
        return out
