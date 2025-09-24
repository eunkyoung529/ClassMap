# 기능 : 질의 확장(학과 사전) → 키워드+벡터 하이브리드 → 마감일 가중 리랭크.
# from datetime import date, datetime
# from typing import List
# from .taxonomy import expand_query_with_taxonomy
# from .store import Item
# from .embed_index import vector_search

# def keyword_filter(items: List[Item], terms: list[str], limit=60) -> set[str]:
#     hits = []
#     low_terms = [t.lower() for t in terms]
#     for it in items:
#         text = " ".join([
#             it.title or "", it.description or "",
#             ",".join(it.categories), ",".join(it.target_jobs), ",".join(it.target_majors)
#         ]).lower()
#         if any(t in text for t in low_terms):
#             hits.append(it.id)
#             if len(hits) >= limit: break
#     return set(hits)

# def merge_and_rerank(query: str, items: List[Item], tax: dict, persist_dir: str, top_k=8) -> List[Item]:
#     terms = expand_query_with_taxonomy(query, tax)
#     kw_ids = keyword_filter(items, terms, 60)
#     vec = vector_search(query, 60, persist_dir)

#     vec_map = {h["id"]: h["score"] for h in vec}
#     id_map = {it.id: it for it in items}

#     cand_ids = set(vec_map.keys()) | kw_ids
#     cands = []
#     for _id in cand_ids:
#         it = id_map.get(_id)
#         if not it:
#             continue
#         score = vec_map.get(_id, 9999.0)
#         # 마감일 가중(가까울수록 상단)
#         if it.deadline:
#             try:
#                 d = datetime.fromisoformat(it.deadline).date()
#                 days = (d - date.today()).days
#                 if 0 <= days <= 14: score *= 0.9
#                 elif days < 0: score *= 1.5
#             except: pass
#         cands.append((score, it))
#     cands.sort(key=lambda x: x[0])
#     return [it for _, it in cands[:top_k]]


# 잘 실행되는 코드

# from __future__ import annotations
# import math
# import numpy as np
# import pandas as pd
# from typing import List, Dict, Any
# from .embed_index import load_index

# BIG_HOSTS = [
#     "google", "구글", "삼성", "samsung", "네이버", "naver", "카카오", "kakao", "lg",
#     "라인", "라인플러스", "과학기술정보통신부", "행정안전부", "고용노동부", "중소벤처기업부",
#     "산업통상자원부", "서울특별시", "국방부", "nipa", "etri"
# ]

# DEV_KWS = [
#     "개발","developer","dev","코딩","프로그래밍","알고리즘","ai","인공지능","데이터","data",
#     "머신러닝","딥러닝","web","웹","백엔드","프론트엔드","server","api","해커톤","보안",
#     "security","임베디드","iot","로봇","게임","클라우드","cloud","블록체인"
# ]

# def _score_host(host: str) -> float:
#     h = (host or "").lower()
#     return 1.5 if any(b in h for b in BIG_HOSTS) else 0.0

# def _score_len(content: str) -> float:
#     L = max(0, len(content or ""))
#     return min(2.0, math.log1p(L) / 3.0)

# def _score_deadline(deadline: str | None) -> float:
#     return 0.3 if deadline else 0.0

# def _kw_score(text: str, kws: List[str]) -> float:
#     t = (text or "").lower()
#     return float(sum(1 for k in kws if k in t))

# def _to_star(score: float) -> float:
#     val = 3.0 + min(2.0, max(0.0, (score / 5.0) * 2.0))
#     return round(val * 10) / 10

# def search(query: str, top_k: int = 6) -> pd.DataFrame:
#     idx = load_index()
#     vec = idx["vectorizer"].transform([query.lower()])
#     sims = (idx["matrix"] @ vec.T).toarray().ravel()  # cosine (TF-IDF 기본 정규화 가정)
#     recs = idx["records"].copy()
#     recs["sim"] = sims

#     # 휴리스틱 보정
#     recs["kw_dev"] = recs["text"].apply(lambda t: _kw_score(t, DEV_KWS))
#     recs["host_bonus"] = recs["host"].apply(_score_host)
#     recs["len_bonus"] = recs["content"].apply(_score_len)
#     recs["dl_bonus"] = recs["deadline"].apply(_score_deadline)

#     # 사용자가 개발/AI 등을 언급하면 DEV 가중
#     wants_dev = any(k in query for k in ["개발","코딩","프로그래밍","알고리즘","ai","인공지능","데이터"])
#     dev_weight = 0.8 if wants_dev else 0.2

#     recs["score"] = (
#         recs["sim"] * 6.0
#         + recs["kw_dev"] * dev_weight
#         + recs["host_bonus"]
#         + recs["len_bonus"]
#         + recs["dl_bonus"]
#     )
#     recs["stars"] = recs["score"].apply(_to_star)

#     recs = recs.sort_values(["score", "stars"], ascending=False).head(top_k).reset_index(drop=True)
#     return recs[["title","host","deadline","field","link","content","stars","score"]]

# import math
# import numpy as np
# import pandas as pd
# from .embed_index import load_index

# BIG_HOSTS = [
#     "google","구글","삼성","samsung","네이버","naver","카카오","kakao","lg","라인","라인플러스",
#     "과학기술정보통신부","행정안전부","고용노동부","중소벤처기업부","산업통상자원부","서울특별시","국방부","nipa","etri"
# ]
# DEV_KWS = ["개발","developer","dev","코딩","프로그래밍","알고리즘","ai","인공지능","데이터","data",
#            "머신러닝","딥러닝","web","웹","백엔드","프론트엔드","server","api","해커톤","보안","security",
#            "임베디드","iot","로봇","게임","클라우드","cloud","블록체인"]

# def _kw_score(t: str, kws) -> float:
#     t = (t or "").lower()
#     return float(sum(1 for k in kws if k.lower() in t))

# def _host_bonus(host: str) -> float:
#     h = (host or "").lower()
#     return 1.5 if any(b in h for b in BIG_HOSTS) else 0.0

# def _len_bonus(content: str) -> float:
#     L = max(0, len(content or ""))
#     return min(2.0, math.log1p(L)/3.0)

# def _dl_bonus(deadline: str | None) -> float:
#     return 0.3 if deadline else 0.0

# def _to_star(score: float) -> float:
#     val = 3.0 + min(2.0, max(0.0, (score/5.0)*2.0))
#     return round(val*10)/10

# def search(query: str, top_k: int = 6) -> pd.DataFrame:
#     idx = load_index()
#     vec = idx["vectorizer"].transform([query.lower()])
#     sims = (idx["matrix"] @ vec.T).toarray().ravel()
#     recs = idx["records"].copy()
#     recs["sim"] = sims

#     wants_dev = any(k in query for k in ["개발","코딩","프로그래밍","알고리즘","ai","인공지능","데이터"])
#     dev_w = 0.8 if wants_dev else 0.2

#     recs["kw_dev"] = recs["text"].apply(lambda t: _kw_score(t, DEV_KWS))
#     recs["score"] = (
#         recs["sim"] * 6.0
#         + recs["kw_dev"] * dev_w
#         + recs["host"].apply(_host_bonus)
#         + recs["content"].apply(_len_bonus)
#         + recs["deadline"].apply(_dl_bonus)
#     )
#     recs["stars"] = recs["score"].apply(_to_star)
#     recs = recs.sort_values(["score","stars"], ascending=False).head(top_k).reset_index(drop=True)
#     return recs


import math
import numpy as np
import pandas as pd
from .embed_index import load_index
from .majors import major_keywords
from .nlp import extract_interests

BIG_HOSTS = [
    "google","구글","삼성","samsung","네이버","naver","카카오","kakao","lg","라인","라인플러스",
    "과학기술정보통신부","행정안전부","고용노동부","중소벤처기업부","산업통상자원부","서울특별시","국방부","nipa","etri"
]

def _contains_any(text: str, kws: list[str]) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in kws)

def _kw_score(text: str, kws: list[str], w: float = 1.0) -> float:
    t = (text or "").lower()
    return w * float(sum(1 for k in kws if k.lower() in t))

def _host_bonus(host: str) -> float:
    h = (host or "").lower()
    return 1.2 if any(b in h for b in BIG_HOSTS) else 0.0

def _len_bonus(content: str) -> float:
    L = max(0, len(content or ""))
    return min(1.5, math.log1p(L)/4.0)

def _dl_bonus(deadline: str | None) -> float:
    return 0.25 if deadline else 0.0

def _to_star(score: float) -> float:
    val = 3.0 + min(2.0, max(0.0, (score/5.0)*2.0))
    return round(val*10)/10

def search_with_profile(user_major: str, user_query: str, top_k: int = 6) -> pd.DataFrame:
    idx = load_index()
    vec = idx["vectorizer"].transform([user_query.lower()])
    sims = (idx["matrix"] @ vec.T).toarray().ravel()

    recs = idx["records"].copy()
    recs["sim"] = sims

    # 전공/관심 키워드 계산
    m_kws = major_keywords(user_major)        # 전공 기반 확장 키워드
    i_kws = extract_interests(user_query)     # 사용자 문장 기반 관심 키워드

    def row_score(row):
        text = row.get("text","")
        title = (row.get("title","") or "").lower()
        field = (row.get("field","") or "").lower()
        content = row.get("content","") or ""

        sim = row["sim"] * 6.0

        # 전공/관심/제목/분야 매칭 가중치
        s_major   = _kw_score(text, m_kws, w=1.6)
        s_interest= _kw_score(text, i_kws, w=2.0)
        s_title   = _kw_score(title, m_kws + i_kws, w=1.5)
        s_field   = _kw_score(field, m_kws + i_kws, w=1.8)

        # 일반 보너스
        s_host = _host_bonus(row.get("host",""))
        s_len  = _len_bonus(content)
        s_dl   = _dl_bonus(row.get("deadline"))

        score = sim + s_major + s_interest + s_title + s_field + s_host + s_len + s_dl

        # 오프토픽 패널티: 전공/관심 키워드가 하나도 없으면 감점
        if not _contains_any(text, m_kws + i_kws):
            score -= 2.0

        return score

    recs["score"] = recs.apply(row_score, axis=1)
    recs["stars"] = recs["score"].apply(_to_star)

    # 전공/관심과 완전 무관한 항목 강제 제거(상황에 따라 완화 가능)
    mask_related = recs["text"].apply(lambda t: _contains_any(t, m_kws + i_kws))
    filtered = recs[mask_related]
    if len(filtered) == 0:
        # 너무 빡세면, 유사도 상위 50개 중에서만 완화 필터
        tmp = recs.sort_values("sim", ascending=False).head(50)
        filtered = tmp

    out = filtered.sort_values(["score","stars"], ascending=False).head(top_k).reset_index(drop=True)
    return out

