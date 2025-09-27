def generate_answer(query: str, hits, deployment: str, client) -> str:
    seen_titles = set()
    unique_hits = []
    for h in hits:
        title = h.get("title")
        if title not in seen_titles:
            unique_hits.append(h)
            seen_titles.add(title)

    context = "\n\n".join([
        ("- 강의명: {title}\n"
         "  교수명: {prof}\n"
         "  수업시간: {time}\n"
         "  전공/교양: {ctype}\n"
         "  수강대상: {target}\n"
         "  개요: {overview}\n"
         "  수업목표: {objectives}\n"
         "  평가방식: {evaluation}\n").format(
            title=h.get("title", "?"),
            prof=h.get("instructor") or h.get("professor") or "?",
            time=h.get("schedule") or h.get("time") or "?",
            ctype=h.get("course_type") or "?",
            target=h.get("target") or "?",
            overview=h.get("overview") or (h.get("text", "")[:500] + "..."),
            objectives=h.get("objectives", "?"),
            evaluation=h.get("evaluation", "?")
        )
        for h in unique_hits
    ])

    prompt = f"""
너는 대학 강의 추천 챗봇이야.
사용자가 원하는 전공/교양 및 조건에 따라 적절한 강의를 추천해줘.

[규칙]
- 각 강의는 반드시 번호 매겨서 출력한다. (예: 1., 2., 3.)
- 각 강의는 동일 과목이 중복되지 않도록 출력한다.
- 과장/추측 금지. 컨텍스트에 있는 정보만 사용.
- 각 강의는 반드시 7개의 항목만 출력한다:
  1. 강의명
  2. 교수명
  3. 수업시간
  4. 전공/교양
  5. 수강대상
  6. 강의 개요 요약
  7. 강의 추천 이유
- 각 항목은 반드시 한 번만 출력한다. (중복 금지)
- "강의 추천 이유"는 반드시 한 문단으로만 작성한다.
- 불필요한 항목명 반복이나 공백 줄은 쓰지 않는다.
- 추천 이유는 반드시 컨텍스트에 포함된 정보만 근거로 작성한다.
- 새로운 학과명이나 수강대상, 과목 특성을 임의로 만들어내지 않는다.

[사용자 질문]
{query}

[컨텍스트(검색 결과)]
{context}
"""

    resp = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=900
    )
    return resp.choices[0].message.content