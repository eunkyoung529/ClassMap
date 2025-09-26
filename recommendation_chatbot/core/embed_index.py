# # 기능 : 문서 임베딩 및 Chroma 벡터 인덱스 생성/검색.
# import os, pickle
# import pandas as pd
# from sklearn.feature_extraction.text import TfidfVectorizer
# from .config import VECTOR_DIR, INDEX_PKL

# def build_index(df: pd.DataFrame) -> None:
#     os.makedirs(VECTOR_DIR, exist_ok=True)
#     vec = TfidfVectorizer(max_features=50000, ngram_range=(1,2), min_df=1)
#     X = vec.fit_transform(df["text"].tolist())
#     payload = {
#         "vectorizer": vec,
#         "matrix": X,
#         "records": df[["title","host","deadline","field","link","content","text"]].reset_index(drop=True),
#     }
#     with open(INDEX_PKL, "wb") as f:
#         pickle.dump(payload, f)

# def load_index():
#     with open(INDEX_PKL, "rb") as f:
#         return pickle.load(f)


# -*- coding: utf-8 -*-
# 기능: Azure 임베딩을 사용한 경량 벡터 인덱스(JSON). 200~수천 건 규모에 적합.

from __future__ import annotations
import json, os, math
from dataclasses import asdict
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from openai import OpenAI
from .store import Item

INDEX_FILE = "items.index.json"

def _client() -> OpenAI:
    # Azure OpenAI: 환경변수 기반 설정
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not api_key or not endpoint:
        raise RuntimeError("Azure OpenAI 환경변수(AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)가 필요합니다.")
    return OpenAI(
        api_key=api_key,
        base_url=f"{endpoint}/openai/deployments/{os.getenv('AZURE_OPENAI_EMBED_DEPLOYMENT')}",
    )

def _embed(texts: List[str]) -> List[List[float]]:
    client = _client()
    resp = client.embeddings.create(input=texts, model=os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT"))
    return [d.embedding for d in resp.data]

def _doc_text(it: Item) -> str:
    parts = [it.title or "", it.host or "", it.description or "", ",".join(it.categories)]
    return " ".join([p for p in parts if p]).strip()

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
    return float(np.dot(a, b) / denom)

class SimpleVectorDB:
    def __init__(self, persist_dir: str):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.persist_dir / INDEX_FILE
        self.ids: List[str] = []
        self.vecs: np.ndarray | None = None
        self.meta: Dict[str, Dict[str, Any]] = {}

    def build(self, items: List[Item]):
        docs = [_doc_text(it) for it in items]
        embs = _embed(docs)
        self.ids = [it.id for it in items]
        self.vecs = np.array(embs, dtype=np.float32)
        self.meta = {it.id: {
            "title": it.title, "host": it.host, "deadline": it.deadline,
            "link": it.link, "type": it.type, "categories": it.categories
        } for it in items}

    def save(self):
        if self.vecs is None:
            raise RuntimeError("인덱스가 비어 있습니다. build() 먼저 호출하세요.")
        data = {
            "ids": self.ids,
            "vecs": self.vecs.tolist(),
            "meta": self.meta
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def load(self):
        if not self.path.exists():
            raise FileNotFoundError(f"인덱스 파일이 없습니다: {self.path}")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.ids = data["ids"]
        self.vecs = np.array(data["vecs"], dtype=np.float32)
        self.meta = data["meta"]

    def search(self, query: str, top_k: int = 40) -> List[Tuple[str, float]]:
        if self.vecs is None:
            raise RuntimeError("인덱스가 로드되지 않았습니다. load() 또는 build()를 호출하세요.")
        qv = np.array(_embed([query])[0], dtype=np.float32)
        sims = self.vecs @ qv / ((np.linalg.norm(self.vecs, axis=1) * (np.linalg.norm(qv) or 1e-8)) + 1e-8)
        # 유사도 내림차순
        idx = np.argsort(-sims)[:top_k]
        return [(self.ids[i], float(sims[i])) for i in idx]

