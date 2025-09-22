# 기능 : 검색 결과를 사람이 읽기 좋은 텍스트로 포맷. (원하면 LLM 요약으로 교체)
from typing import List
from .store import Item

def render_plain(query: str, items: List[Item]) -> str:
    lines = [f'질문: "{query}"', "추천 결과:"]
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. {it.title} - {it.host or ''} (마감: {it.deadline or '미정'})")
        if it.link:
            lines.append(f"   {it.link}")
    return "\n".join(lines)

# OpenAI 요약을 쓰고 싶다면 아래 주석을 해제하고 OPENAI_API_KEY 환경변수를 설정하세요.
# import os
# from openai import OpenAI
# def render_llm(query: str, items: List[Item]) -> str:
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         return render_plain(query, items)
#     client = OpenAI(api_key=api_key)
#     bullets = "\n".join([f"- {it.title} | {it.host or ''} | {it.deadline or '미정'} | {it.link or ''}" for it in items])
#     system = "너는 추천 비서다. 사용자 학과/진로에 맞춘 공모전/대외활동을 간결히 추천해라."
#     user = f'사용자 입력: "{query}"\n\n[후보]\n{bullets}\n\n각 항목당 한 줄 적합 이유도 덧붙여줘.'
#     resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":system},{"role":"user","content":user}])
#     return resp.choices[0].message.content.strip()
