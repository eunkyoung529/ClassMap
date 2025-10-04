# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Tuple
import os
from openai import OpenAI
from .store import Item

def _client() -> OpenAI | None:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deploy = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
    if not (api_key and endpoint and deploy):
        return None
    return OpenAI(api_key=api_key, base_url=f"{endpoint}/openai/deployments/{deploy}")

def llm_rerank(query: str, items: List[Item], top_k: int = 10) -> List[Item]:
    """
    Azure Chat LLM을 이용해 후보 재정렬. 임베딩 배포 없이 가능.
    - 입력: 사용자 질의 + (title, host, deadline, desc)
    - 출력: 상위 top_k만 리스트로
    """
    cli = _client()
    if not cli or not items:
        return items[:top_k]

    # 프롬프트: 간결한 리스트 랭킹. JSON id 배열로만 응답 유도.
    system = (
        "너는 공모전 추천 랭커다. 사용자 의도(전공/키워드/행동)를 고려해 가장 관련 높은 순으로 재정렬해라. "
        "영문 에세이/번역/토론/설계/임상 등 의도어가 일치하는 항목을 최우선으로 하고, 무관한 콘텐츠/영상/마케팅-only 항목은 뒤로."
    )
    # 후보를 compact 텍스트로
    lines = []
    for it in items[:30]:  # LLM에 과부하 방지
        desc_snip = (it.description or "")[:200].replace("\n"," ")
        cat = ",".join(it.categories)
        lines.append(f"{it.id}\t{it.title}\t{cat}\t{desc_snip}")
    user = (
        f"질의: {query}\n"
        "다음의 후보들(id, title, categories, desc_snippet)을 가장 관련 높은 순으로 최대 10개 id만 JSON 배열로 출력해.\n"
        "예: [\"id1\",\"id2\",...]\n\n" + "\n".join(lines)
    )
    try:
        r = cli.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
            temperature=0.0, max_tokens=200
        )
        text = (r.choices[0].message.content or "").strip()
        import json
        ids = json.loads(text)
        if not isinstance(ids, list):
            return items[:top_k]
        idset = [i for i in ids if isinstance(i, str)]
        id2item = {it.id: it for it in items}
        ranked = [id2item[i] for i in idset if i in id2item]
        # 누락 채우기
        for it in items:
            if it not in ranked:
                ranked.append(it)
        return ranked[:top_k]
    except Exception:
        return items[:top_k]
