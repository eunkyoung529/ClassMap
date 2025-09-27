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
