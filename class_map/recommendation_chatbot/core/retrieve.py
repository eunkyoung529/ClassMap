# # # 기능 : 질의 확장(학과 사전) → 키워드+벡터 하이브리드 → 마감일 가중 리랭크.

from __future__ import annotations
import re
from typing import List, Tuple, Optional, Dict, Set
from datetime import datetime  # (미사용이지만 남겨둬도 무방)

from .store import Item
from .majors import MajorEntry, expand_terms_for_major
from .preference import extract_preferences, score_by_preferences

ARCH_CORE_ANY = [   
    "건축", "설계", "현상설계", "도면", "bim", "cad", "포트폴리오",
    "렌더링", "모형", "조형", "스튜디오", "마스터플랜", "건축공모"
]

def extract_intent(user_text: str) -> Dict[str, List[str]]:
    text = (user_text or "").lower()
    ESSAY  = ["에세이","essay","영문 에세이","영문에세이","영어 에세이","영어에세이","영작","작문","글쓰기","writing"]
    TRANSL = ["번역","translation","번역대회","translating","번역공모"]
    ACADEM = ["논문","paper","학술","conference","학회","학술논문"]
    SPEECH = ["스피치","speech","연설","발표"]
    DEBATE = ["토론","debate","디베이트","토의","모의법정","moot court","moot","모의재판","변론대회"]
    BUILD  = ["설계","디자인","도면","cad","bim","렌더링","포트폴리오","모형","조형","스튜디오","마스터플랜","현상설계","건축공모"]

    NEG = ["콘텐츠","영상","사진","카드뉴스","포스터","캐릭터","창업","경영혁신","환경교육","보안","과학수사","베이킹",
           "디자인 공모전","앱개발","메이커","제조","로봇","해커톤"]

    explicit_excludes = []
    for m in re.finditer(r"(?:제외|빼고)\s*([가-힣A-Za-z ]{1,20})", user_text):
        explicit_excludes.append(m.group(1).strip())

    must: List[str] = []
    prefer: List[str] = []
    exclude: List[str] = NEG + explicit_excludes

    if any(w in text for w in ESSAY):
        must += ["에세이","essay"]; prefer += ESSAY; exclude += SPEECH
    if any(w in text for w in TRANSL):
        must += ["번역","translation"]; prefer += TRANSL
    if any(w in text for w in ACADEM):
        must += ["논문","paper","학술"]; prefer += ACADEM
    if any(w in text for w in DEBATE):
        must += ["토론","debate","모의법정","moot"]; prefer += DEBATE; exclude += SPEECH

    if any(w in text for w in ["건축","설계","현상설계","bim","cad","렌더링","포트폴리오"]):
        must += ["설계"]; prefer += BUILD

    if any(w in text for w in ["영문","영어","english"]):
        prefer += ["영문","영어","english"]

    def uniq(x: List[str]) -> List[str]:
        seen: Set[str] = set(); out: List[str] = []
        for t in x:
            t=t.strip()
            if t and t not in seen:
                seen.add(t); out.append(t)
        return out

    return {"must": uniq(must), "prefer": uniq(prefer), "exclude": uniq(exclude)}

def _text_blob(it: Item) -> str:
    return " ".join([(it.title or ""), (it.host or ""), (it.description or ""), ",".join(it.categories)]).lower()

def _keyword_hits(it: Item, terms: List[str]) -> int:
    text = _text_blob(it)
    low_terms = [tn.lower() for tn in terms]
    return sum(1 for tn in low_terms if tn and tn in text)

def _contains_all(text: str, terms: List[str]) -> bool:
    if not terms: return True
    t = text.lower()
    return all(tn.lower() in t for tn in terms)

def _contains_any(text: str, terms: List[str]) -> bool:
    if not terms: return True
    t = text.lower()
    return any(tn.lower() in t for tn in terms)

def hybrid_search(
    user_text: str,
    items: List[Item],
    major: Optional[MajorEntry],
    major_jobs: List[str],
    bm25,        # BM25Index
    chroma,      # ChromaIndex | None
    top_k: int = 10,
    w_bm25: float = 0.85,
    w_chroma: float = 0.15
) -> Tuple[List[Item], Optional[Item], List[str]]:
    intent = extract_intent(user_text)
    must, prefer_terms, exclude_terms = intent["must"], intent["prefer"], intent["exclude"]
    prefs = extract_preferences(user_text)

    terms = expand_terms_for_major(user_text, major, major_jobs)
    for t in prefer_terms:
        if t not in terms: terms.append(t)

    bm25_scores: Dict[str, float] = {}
    for _id, s in bm25.search(terms, top_k=160):
        bm25_scores[_id] = s
    if bm25_scores:
        mx = max(bm25_scores.values()) or 1.0
        for k in list(bm25_scores.keys()):
            bm25_scores[k] = bm25_scores[k] / mx  # 0~1

    chroma_scores: Dict[str, float] = {}
    if chroma:
        for _id, dist in chroma.search(" ".join(terms) or user_text, top_k=80):
            chroma_scores[_id] = 1.0 / (1.0 + max(0.0, dist))  # 0~1

    kw_ids: Set[str] = set()
    kw_bonus: Dict[str, float] = {}
    title_bonus: Dict[str, float] = {}
    exclude_penalty: Dict[str, float] = {}

    for it in items:
        text = _text_blob(it)
        hits = _keyword_hits(it, terms)
        if hits > 0:
            kw_ids.add(it.id)
            kw_bonus[it.id] = 1.0 - min(hits, 6) * 0.03  # 최대 18% 보너스
        title_low = (it.title or "").lower()
        tb = 1.0
        if must and _contains_all(title_low, must):
            tb *= 0.60
        elif _contains_any(title_low, prefer_terms):
            tb *= 0.80
        title_bonus[it.id] = tb
        ep = 1.0
        if _contains_any(text, exclude_terms) and not _contains_all(text, must):
            ep *= 1.08
        exclude_penalty[it.id] = ep

    id_map = {it.id: it for it in items}
    cand_ids = set(bm25_scores.keys()) | set(chroma_scores.keys()) | kw_ids or {it.id for it in items}

    if must:
        strict = [i for i in cand_ids if _contains_all(_text_blob(id_map[i]), must)]
        if strict:
            cand_ids = set(strict)
        else:
            relaxed = [i for i in cand_ids if _contains_any((id_map[i].title or "").lower(), prefer_terms)]
            cand_ids = set(relaxed)  # 비면 그대로 비게 둠

    is_arch_query = any(w in (user_text or "").lower() for w in ["건축","설계","현상설계","bim","cad","렌더링","포트폴리오"])
    if is_arch_query:
        guarded = []
        for i in cand_ids:
            if _contains_any(_text_blob(id_map[i]), ARCH_CORE_ANY):
                guarded.append(i)
        cand_ids = set(guarded)
        if not cand_ids:
            return [], None, prefs

    major_boost_terms: List[str] = []
    if major:
        m = major.name
        if "법" in m:
            major_boost_terms += ["모의법정","모의재판","변론","법정변론","판례","케이스브리프","법률에세이","인권논문","로스쿨","토론"]
        if "영문" in m or "영어" in m:
            major_boost_terms += ["essay","에세이","영문","번역","영작","writing","translation","speech","debate"]
        if "건축" in m:
            major_boost_terms += ["설계","현상설계","포트폴리오","렌더링","도면","모형","bim","cad","스튜디오","건축공모","졸업전시"]
        if "심리" in m:
            major_boost_terms += ["심리","상담","임상","심리평가","연구포스터","논문","학술대회","실습","봉사","케이스스터디"]

    def major_bonus(text_low: str) -> float:
        if not major_boost_terms: return 1.0
        return 0.85 if _contains_any(text_low, major_boost_terms) else 1.0

    scored: List[Tuple[float, Item]] = []
    for i in cand_ids:
        it = id_map[i]
        b = bm25_scores.get(i, 0.0)
        c = chroma_scores.get(i, 0.0)
        sim = w_bm25 * b + w_chroma * c 
        score = 0.3 - sim
        score *= kw_bonus.get(i, 1.0)
        score *= title_bonus.get(i, 1.0)
        score *= exclude_penalty.get(i, 1.0)
        score *= major_bonus(_text_blob(it))
        score *= score_by_preferences((it.title or "") + " " + (it.description or ""), prefs)
        if it.rating is not None:
            score *= (1.0 - min(it.rating, 5.0) * 0.02)
        scored.append((score, it))

    scored.sort(key=lambda x: x[0])
    ranked = [it for _, it in scored[:max(top_k, 10)]]

    famous = None
    try:
        famous = max(ranked, key=lambda x: (x.rating or 0.0)) if ranked else None
    except ValueError:
        famous = ranked[0] if ranked else None

    return ranked[:10], famous, prefs
