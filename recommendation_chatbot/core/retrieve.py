# 기능 : 질의 확장(학과 사전) → 키워드+벡터 하이브리드 → 마감일 가중 리랭크.
from datetime import date, datetime
from typing import List
from .taxonomy import expand_query_with_taxonomy
from .store import Item
from .embed_index import vector_search

def keyword_filter(items: List[Item], terms: list[str], limit=60) -> set[str]:
    hits = []
    low_terms = [t.lower() for t in terms]
    for it in items:
        text = " ".join([
            it.title or "", it.description or "",
            ",".join(it.categories), ",".join(it.target_jobs), ",".join(it.target_majors)
        ]).lower()
        if any(t in text for t in low_terms):
            hits.append(it.id)
            if len(hits) >= limit: break
    return set(hits)

def merge_and_rerank(query: str, items: List[Item], tax: dict, persist_dir: str, top_k=8) -> List[Item]:
    terms = expand_query_with_taxonomy(query, tax)
    kw_ids = keyword_filter(items, terms, 60)
    vec = vector_search(query, 60, persist_dir)

    vec_map = {h["id"]: h["score"] for h in vec}
    id_map = {it.id: it for it in items}

    cand_ids = set(vec_map.keys()) | kw_ids
    cands = []
    for _id in cand_ids:
        it = id_map.get(_id)
        if not it:
            continue
        score = vec_map.get(_id, 9999.0)
        # 마감일 가중(가까울수록 상단)
        if it.deadline:
            try:
                d = datetime.fromisoformat(it.deadline).date()
                days = (d - date.today()).days
                if 0 <= days <= 14: score *= 0.9
                elif days < 0: score *= 1.5
            except: pass
        cands.append((score, it))
    cands.sort(key=lambda x: x[0])
    return [it for _, it in cands[:top_k]]
