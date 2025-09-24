import os
from typing import List, Optional
from .store import Item

def render_plain(user_name: str, query: str, items: List[Item], famous: Optional[Item], prefs: List[str]) -> str:
    lines = [f'{user_name}님, 요청하신 "{query}"에 대한 추천입니다.']
    if prefs:
        lines.append(f"선호 파악: {', '.join(prefs)}")
    lines.append("")
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. {it.title} - {it.host or ''} (마감: {it.deadline or '미정'})")
        if it.link: lines.append(f"   {it.link}")
    if famous:
        lines.append("")
        lines.append(f"가장 유명한 활동(별점/인기 기준): **{famous.title}**")
    return "\n".join(lines)

# Azure OpenAI (chat) 사용
def render_azure(user_name: str, query: str, items: List[Item], famous: Optional[Item], prefs: List[str]) -> str:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key  = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # 예: gpt-4o-mini
    if not (endpoint and api_key and deployment):
        return render_plain(user_name, query, items, famous, prefs)

    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(api_key=api_key, api_version="2024-08-01-preview", azure_endpoint=endpoint)

        items_md = "\n".join([
            f"- {it.title} | {it.host or ''} | 마감:{it.deadline or '미정'} | {it.link or ''}"
            for it in items
        ])
        famous_md = famous.title if famous else "N/A"
        system = (
            "너는 추천 비서다. 아래 후보를 바탕으로 사용자 전공/선호에 맞는 공모전/대외활동을 제안하라. "
            "반드시: (1) 추천 리스트, (2) 가장 유명한 활동 1개, (3) 추천 이유(선호와 연결)를 포함하라."
        )
        user = (
            f"사용자: {user_name}\n"
            f"요청: \"{query}\"\n"
            f"선호: {', '.join(prefs) if prefs else '미입력'}\n"
            f"[후보]\n{items_md}\n"
            f"가장 유명한 후보: {famous_md}\n"
            "응답 형식 예시:\n"
            "네. 알겠습니다. {전공/선호}에 관련한 추천은 ... 이고, 가장 유명한 활동은 ... 입니다. "
            "추천 이유: ... 님의 선호(OOO)와 활동의 특성(XXX)이 잘 맞습니다."
        )
        resp = client.chat.completions.create(
            model=deployment,
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
            temperature=0.5
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return render_plain(user_name, query, items, famous, prefs)
