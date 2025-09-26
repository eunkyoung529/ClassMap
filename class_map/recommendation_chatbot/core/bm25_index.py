# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from .store import Item

_TOKEN = re.compile(r"[가-힣A-Za-z0-9]+")

def _tokenize(text: str) -> List[str]:
    return _TOKEN.findall((text or "").lower())

def _doc_text(it: Item) -> str:
    return " ".join([
        it.title or "", it.host or "", ",".join(it.categories), it.description or ""
    ])

class BM25Index:
    def __init__(self, items: List[Item]):
        self.items = items
        self.docs = [_tokenize(_doc_text(it)) for it in items]
        self.bm25 = BM25Okapi(self.docs)

    def search(self, query_terms: List[str], top_k: int = 60) -> List[Tuple[str, float]]:
        q = _tokenize(" ".join(query_terms))
        if not q:
            return []
        scores = self.bm25.get_scores(q)
        idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self.items[i].id, float(scores[i])) for i in idxs]
