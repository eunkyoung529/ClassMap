# # -*- coding: utf-8 -*-
# # 기능: (1) 전공 키워드 보강용 LLM (2) 추천 결과 요약 응답 (Azure)
# # 키 미설정 시 plain 렌더로 폴백

# from __future__ import annotations
# import os
# from typing import List, Optional
# from openai import OpenAI
# from .store import Item

# def _client() -> Optional[OpenAI]:
#     api_key = os.getenv("AZURE_OPENAI_API_KEY")
#     endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
#     deploy = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
#     if not (api_key and endpoint and deploy):
#         return None
#     return OpenAI(
#         api_key=api_key,
#         base_url=f"{endpoint}/openai/deployments/{deploy}",
#     )

# def generate_major_keywords(major_name: str, fallback: List[str], n: int = 18) -> List[str]:
#     """
#     전공명이 있으나 표준데이터에 관련직업명이 비었을 때 보강.
#     """
#     cli = _client()
#     if not cli:
#         return fallback
#     sys = "너는 전공-직무 연결에 능한 조교다. 한국 대학 전공과 연관된 직무/활동/키워드를 한글 단어로만, 쉼표로 구분해 짧게 나열해."
#     user = f'전공: "{major_name}"\n출력: 직무/활동 키워드 {n}개 내외 (쉼표 구분, 설명 금지)'
#     try:
#         r = cli.chat.completions.create(
#             model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
#             messages=[{"role":"system","content":sys},{"role":"user","content":user}],
#             temperature=0.2, max_tokens=300,
#         )
#         text = r.choices[0].message.content.strip()
#         # 쉼표 분해
#         out = [t.strip() for t in text.replace("\n"," ").split(",")]
#         out = [t for t in out if t and len(t) <= 20]
#         # 폴백과 합치되 중복 제거
#         seen=set(); merged=[]
#         for t in out + fallback:
#             if t not in seen:
#                 seen.add(t); merged.append(t)
#         return merged[:n]
#     except Exception:
#         return fallback

# def render_plain(user_name: str, query: str, items: List[Item], famous: Optional[Item], prefs: List[str]) -> str:
#     lines = [f'{user_name}님, 요청하신 "{query}" 관련 추천입니다.']
#     if prefs:
#         lines.append(f"선호 파악: {', '.join(prefs)}")
#     lines.append("")
#     for i, it in enumerate(items, 1):
#         lines.append(f"{i}. {it.title} - {it.host or ''} (마감: {it.deadline or '미정'})")
#         if it.link:
#             lines.append(f"   {it.link}")
#     if famous:
#         lines.append("")
#         lines.append(f"가장 유명/대표: {famous.title}")
#     return "\n".join(lines)

# def render_with_llm(user_name: str, query: str, items: List[Item], famous: Optional[Item], prefs: List[str]) -> str:
#     cli = _client()
#     if not cli:
#         return render_plain(user_name, query, items, famous, prefs)
#     bullets = "\n".join([f"- {it.title} | {it.host or ''} | {it.deadline or '미정'} | {it.link or ''}" for it in items])
#     famous_md = famous.title if famous else "없음"
#     sys = "너는 한국어 추천 비서다. 대학 전공/진로와 관련된 공모전·대외활동을 간결하고 자연스럽게 정리한다."
#     user = (
#         f"사용자: {user_name}\n"
#         f"요청: {query}\n"
#         f"선호: {', '.join(prefs) if prefs else '파악불가'}\n\n"
#         f"[후보]\n{bullets}\n\n"
#         f"대표 후보: {famous_md}\n\n"
#         "출력은 말투 자연스럽게 6~10줄, 각 항목은 한 줄 요약 + 링크. 선호가 있으면 추천 이유에 살짝 반영."
#     )
#     try:
#         r = cli.chat.completions.create(
#             model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
#             messages=[{"role":"system","content":sys},{"role":"user","content":user}],
#             temperature=0.5, max_tokens=650,
#         )
#         return r.choices[0].message.content.strip()
#     except Exception:
#         return render_plain(user_name, query, items, famous, prefs)



# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from typing import List, Optional
from openai import OpenAI
from .store import Item

def _client() -> Optional[OpenAI]:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deploy = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
    if not (api_key and endpoint and deploy):
        return None
    return OpenAI(api_key=api_key, base_url=f"{endpoint}/openai/deployments/{deploy}")

def render_plain(user: str, query: str, items: List[Item], famous: Optional[Item], prefs, hide_deadline: bool = False) -> str:
    lines = []
    lines.append(f'{user}님, 요청하신 "{query}" 관련 추천입니다.\n')
    if not items:
        lines.append("조건에 맞는 항목을 찾지 못했습니다. 키워드를 조금 넓혀서 다시 시도해 보세요.")
        return "\n".join(lines)

    for idx, it in enumerate(items[:10], start=1):
        lines.append(f"{idx}. {it.title} - {it.host or '주최 미상'}")
        if it.link:
            lines.append(f"   {it.link}")
    if famous:
        lines.append(f"\n가장 유명/대표: {famous.title}")
    return "\n".join(lines)

def render_with_llm(user: str, query: str, items: List[Item], famous: Optional[Item], prefs, hide_deadline: bool = False) -> str:
    cli = _client()
    if not cli:
        return render_plain(user, query, items, famous, prefs, hide_deadline=True)

    sys = (
        "너는 공모전/대외활동 추천 비서다. 아래 후보를 간결한 목록으로 정리하라. "
        "항목당 '제목 - 주최'만 보여주고, 마감일은 표시하지 마라. "
        "링크가 있으면 다음 줄에 URL만 추가하라. 10개까지만 출력한다."
    )
    body = []
    for it in items[:10]:
        body.append(f"- {it.title} — host={it.host or ''} — link={it.link or ''}")
    user_msg = f'사용자 질의: "{query}"\n후보:\n' + "\n".join(body)

    try:
        r = cli.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[{"role":"system","content":sys},{"role":"user","content":user_msg}],
            temperature=0.2,
            max_tokens=700
        )
        return (r.choices[0].message.content or "").strip()
    except Exception:
        return render_plain(user, query, items, famous, prefs, hide_deadline=True)
