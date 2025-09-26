# 기능 : 학과 CSV로 학과↔직무 사전 생성/저장, 로딩, 질의어 확장.
from __future__ import annotations

MAJOR_KEYWORDS = {
    "컴퓨터": ["개발","프로그래밍","ai","데이터","알고리즘","보안","해커톤","웹","백엔드","프론트엔드"],
    "소프트웨어": ["개발","프로그래밍","ai","데이터","웹","앱"],
    "전기": ["임베디드","iot","로봇"],
    "산업": ["데이터","ai","최적화"],
    # 필요시 확장
}

def expand_query_with_major(major: str, base_query: str) -> str:
    hit = []
    for key, kws in MAJOR_KEYWORDS.items():
        if key in major:
            hit.extend(kws)
    if hit:
        return base_query + " " + " ".join(sorted(set(hit)))
    return base_query
