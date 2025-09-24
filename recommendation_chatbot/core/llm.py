# 기능 : 검색 결과를 사람이 읽기 좋은 텍스트로 포맷. (원하면 LLM 요약으로 교체)
import os
import json
import textwrap
import requests
from typing import List, Dict
from .config import (
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
    MAX_CTX,
)
from .nlp import normalize_text  # 간단 정규화에 사용

RC_DEBUG = os.environ.get("RC_DEBUG", "0") == "1"

# -------------------------------------------------
# Azure Chat Completions 사용 여부/헬스체크
# -------------------------------------------------
def _use_llm() -> bool:
    return bool(AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT)

def ping_azure() -> str:
    if not _use_llm():
        return "LLM DISABLED (missing/invalid .env)"
    try:
        _ = _chat_completion([{"role": "user", "content": "ping"}], temperature=0.0, max_tokens=4)
        return "LLM OK (Azure Chat Completions reachable)"
    except Exception as e:
        return f"LLM ERROR: {e}"

def _chat_completion(messages: list[dict], temperature: float = 0.3, max_tokens: int = 800) -> str:
    url = (
        f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}"
        f"/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions"
        f"?api-version={AZURE_OPENAI_API_VERSION}"
    )
    headers = {"Content-Type": "application/json", "api-key": AZURE_OPENAI_KEY}
    payload = {
        "messages": messages,
        "temperature": temperature,
        "top_p": 1.0,
        "max_tokens": max_tokens,
        "response_format": {"type": "text"},
    }
    if RC_DEBUG:
        print("[LLM] POST", url)
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

# -------------------------------------------------
# 전공/관심 → 키워드 확장 (LLM)
# -------------------------------------------------
def expand_keywords_with_llm(user_major: str, interest_text: str = "") -> List[str]:
    """
    전공명 + (선택)관심문장 -> JSON 형태의 키워드 리스트를 생성.
    LLM 미설정 시 간단 폴백으로 동작.
    """
    major = normalize_text(user_major)
    interests = normalize_text(interest_text)

    if not _use_llm():
        # 폴백: 단어 토큰 몇 개만 추출
        base = f"{major} {interests}".lower()
        tokens = [t for t in base.replace("/", " ").split() if len(t) >= 2]
        # 과도 확장 방지
        uniq = []
        seen = set()
        for t in tokens:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        return uniq[:12]

    system = "You generate domain keywords for contests. Output JSON ONLY: {\"keywords\": [\"...\"]}."
    user = textwrap.dedent(f"""
    Major: {major}
    Interests: {interests}

    Generate 8~12 Korean keywords closely related to the major and interests,
    focusing on contest/activity themes (예: 번역, 통번역, 저널리즘, 에세이, 스피치, 토론, 국제교류, 콘텐츠 제작 등).
    ONE-LINE JSON ONLY.
    """).strip()

    try:
        txt = _chat_completion(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
            max_tokens=200,
        )
        data = json.loads(txt)
        kws = [normalize_text(x) for x in data.get("keywords", []) if x]
        # 중복 제거
        seen, out = set(), []
        for w in kws:
            if w and w not in seen:
                seen.add(w)
                out.append(w)
        return out[:12]
    except Exception:
        # 파싱 실패 시 폴백
        base = f"{major} {interests}".lower()
        tokens = [t for t in base.replace("/", " ").split() if len(t) >= 2]
        seen, out = set(), []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out[:10]

# -------------------------------------------------
# LLM 기반 재랭킹
# -------------------------------------------------
def rerank_with_llm(user_major: str, user_query: str, items: List[Dict], top_k: int = 6) -> List[int]:
    """
    items: [{id:int, title, field, host, content, score, stars, deadline, link}]
    → 전공/관심과의 관련도로 상위 id 순서를 반환
    """
    if not _use_llm():
        return [it["id"] for it in items[:top_k]]

    system = "Re-rank contest items by relevance to the user's major & interests. Output JSON ONLY: {\"order\": [ids...]}"
    # 컨텍스트 축약
    lines = []
    for it in items[:MAX_CTX * 2]:
        dl = it.get("deadline") or "상시/미정"
        snippet = (it.get("content", "") or "")[:220].replace("\n", " ").replace("\r", " ")
        lines.append(
            f'{{"id":{it["id"]},"title":"{it["title"]}","field":"{it.get("field","")}","host":"{it.get("host","")}","deadline":"{dl}","stars":{it.get("stars",0)},"snippet":"{snippet}"}}'
        )
    ctx = "[\n" + ",\n".join(lines) + "\n]"

    user = textwrap.dedent(f"""
    UserMajor: {user_major}
    UserQuery: {user_query}

    ITEMS(JSON):
    {ctx}

    Return IDs in best-to-worst order strictly as JSON (no commentary).
    """).strip()

    try:
        txt = _chat_completion(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
            max_tokens=200,
        )
        data = json.loads(txt)
        order = data.get("order", [])
        known = {it["id"] for it in items}
        order = [i for i in order if i in known]
        if not order:
            return [it["id"] for it in items[:top_k]]
        return order[:top_k]
    except Exception:
        return [it["id"] for it in items[:top_k]]

# -------------------------------------------------
# 답변 생성
# -------------------------------------------------
def build_system_prompt() -> str:
    return textwrap.dedent("""
    당신은 대학생을 위한 공모전/대외활동 추천 어시스턴트입니다.
    - 제공된 CONTEXT(제목, 주최, 마감일, 링크, 요약)만 사용해 응답하세요. 추정/환각 금지.
    - 사용자 전공/관심과 무관한 항목은 제외하세요. 거의 없으면 주제적으로 인접한 항목만 최소 확장하세요.
    - 결과는 한국어로 간결하게 쓰고, 링크와 마감일(없으면 '상시/미정')을 명시하세요.
    - 5~6개를 나열하고, 마지막에 '가장 유명한(별점 최고)' 1개를 한 문장 이유와 함께 강조하세요.
    """).strip()

def format_context_rows(rows: List[Dict]) -> str:
    lines = []
    for i, r in enumerate(rows, start=1):
        dl = r.get("deadline") or "상시/미정"
        lines.append(
            f"[{i}] 제목: {r['title']} | 주최: {r['host']} | 마감일: {dl} | 별점: {r['stars']}/5.0 | 링크: {r.get('link','')}\n"
            f"요약: { (r.get('content','') or '')[:300] }"
        )
    return "\n\n".join(lines)

def generate_answer(user_name: str, user_major: str, user_query: str, recs_df) -> str:
    rows = recs_df.head(MAX_CTX).to_dict(orient="records")
    context = format_context_rows(rows)
    sys_prompt = build_system_prompt()

    user_prompt = textwrap.dedent(f"""
    사용자 이름: {user_name}
    사용자 전공: {user_major}
    사용자 요청: {user_query}

    CONTEXT:
    {context}

    지침:
    1) 전공/관심과 직접 관련된 항목들만 추천 리스트(5~6개)를 작성하세요.
    2) 각 항목은 '제목 - 한줄 요약. 마감일: OO / 링크: URL' 형식으로 간결하게 서술하세요.
    3) 마지막 줄에 '가장 유명한(별점 최고): **제목** — 한 문장 이유'를 써주세요.
    """).strip()

    try:
        return _chat_completion(
            [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.3,
            max_tokens=900,
        )
    except Exception:
        # LLM 호출 실패 시 폴백
        bullets = []
        for r in rows:
            dl = r.get("deadline") or "상시/미정"
            bullets.append(f"- {r['title']} — 마감일:{dl} / 링크:{r.get('link','')}")
        top = rows[0] if rows else None
        tail = ""
        if top:
            tail = f"\n\n가장 유명한(별점 최고): **{top['title']}** — 전공/관심과의 관련도가 높습니다."
        return "\n".join(bullets) + tail


