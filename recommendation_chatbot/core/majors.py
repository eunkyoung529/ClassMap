# import os
# import re
# from pathlib import Path
# import pandas as pd
# from .config import MAJORS_CSV

# # 환경변수로 특정 시트/컬럼을 지정할 수 있습니다(엑셀일 때 유용)
# ENV_SHEET = os.environ.get("RC_MAJORS_SHEET", "").strip()
# ENV_COL   = os.environ.get("RC_MAJORS_COL", "").strip()

# STATUS_WORDS = {"기존", "폐과", "신설", "변경", "통합", "비고", "상태", "구분"}

# # -----------------------------
# # 내부: 전공 테이블 읽기 (CSV/엑셀 자동 판별)
# # -----------------------------
# def _read_table_any(path: str) -> dict[str, pd.DataFrame]:
#     """
#     엑셀(.xlsx/.xls)은 모든 시트를 dict로, CSV는 단일 시트를 dict로 반환.
#     반환 형태: {'sheetname': df}
#     """
#     p = Path(path)
#     if p.suffix.lower() in [".xlsx", ".xls"]:
#         if ENV_SHEET:
#             df = pd.read_excel(path, sheet_name=ENV_SHEET, engine="openpyxl" if p.suffix.lower()==".xlsx" else None)
#             return {ENV_SHEET: df}
#         dfs = pd.read_excel(path, sheet_name=None, engine="openpyxl" if p.suffix.lower()==".xlsx" else None)
#         return {str(k): v for k, v in dfs.items()}

#     # CSV: 여러 인코딩 시도
#     for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
#         try:
#             df = pd.read_csv(path, encoding=enc)
#             return {"csv": df}
#         except Exception:
#             continue

#     # CSV 확장자지만 실은 엑셀 바이너리인 경우 마지막 시도
#     try:
#         df = pd.read_excel(path, engine="openpyxl")
#         return {"excel_from_csv": df}
#     except Exception as e:
#         raise RuntimeError(f"전공 파일을 읽을 수 없습니다: {path}\n{e}")

# def _korean_ratio(s: str) -> float:
#     if not isinstance(s, str) or not s:
#         return 0.0
#     total = len(s)
#     kor = sum(1 for ch in s if '\uac00' <= ch <= '\ud7a3')
#     return kor / total if total else 0.0

# def _score_column(series: pd.Series) -> float:
#     """
#     전공명일 가능성 점수: 한글 비율, 유일값 수, 평균 길이 등으로 휴리스틱 스코어 계산
#     """
#     try:
#         s = series.dropna().astype(str).head(200)
#     except Exception:
#         return -1e9
#     if s.empty:
#         return -1e9

#     uniq = s.unique()
#     uniq_count = len(uniq)
#     avg_len = s.map(len).mean()
#     kor_ratio = s.map(_korean_ratio).mean()
#     status_hits = sum(1 for v in uniq if str(v).strip() in STATUS_WORDS)
#     status_penalty = status_hits / max(1, uniq_count)

#     score = (
#         kor_ratio * 3.0
#         + (min(uniq_count, 200) / 200.0) * 2.0
#         + (min(avg_len, 12) / 12.0) * 1.0
#         - status_penalty * 2.5
#     )
#     return float(score)

# def _choose_major_column(df: pd.DataFrame) -> str:
#     cols = list(df.columns)
#     # 1) 환경변수 우선
#     if ENV_COL and ENV_COL in cols:
#         return ENV_COL
#     # 2) 컬럼명 키워드 매칭 우선
#     preferred = [c for c in cols if any(k in str(c) for k in ["학과","전공","학부","계열","과(학과)","학과명","학과(전공)"])]
#     if preferred:
#         return preferred[0]
#     # 3) 점수 기반 탐색
#     scored = sorted(((c, _score_column(df[c])) for c in cols), key=lambda x: x[1], reverse=True)
#     return scored[0][0]

# # -----------------------------
# # 공개 API
# # -----------------------------
# def load_majors() -> pd.DataFrame:
#     """
#     majors.csv/xlsx를 읽어 전공명 테이블 반환: columns = [name, norm]
#     """
#     tables = _read_table_any(MAJORS_CSV)
#     best_df = None; best_col = None; best_score = -1e9

#     for _, df in tables.items():
#         if df is None or df.empty:
#             continue
#         try:
#             col = _choose_major_column(df)
#             score = _score_column(df[col])
#             if score > best_score:
#                 best_score = score
#                 best_df = df
#                 best_col = col
#         except Exception:
#             continue

#     if best_df is None:
#         raise RuntimeError("학과(전공) 컬럼을 자동 탐지하지 못했습니다. .env의 RC_MAJORS_SHEET/RC_MAJORS_COL을 지정하세요.")

#     s = best_df[best_col].astype(str).fillna("")
#     # 불필요한 상태 단어 제거 + 공백행 제거
#     s = s[~s.str.strip().isin(STATUS_WORDS)]
#     s = s[s.str.strip() != ""]

#     out = pd.DataFrame()
#     out["name"] = s
#     out["norm"] = out["name"].str.replace(r"\s+", "", regex=True).str.lower()
#     out = out.drop_duplicates("norm").reset_index(drop=True)
#     return out

# def major_keywords(user_major: str, user_interest_text: str = "") -> list[str]:
#     """
#     전공명 + (선택)사용자 취향문장 -> LLM이 키워드 자동 생성.
#     순환 임포트를 피하기 위해 여기서 지연 임포트 합니다.
#     """
#     # 지연 임포트(순환 방지)
#     from .llm import expand_keywords_with_llm

#     major = (user_major or "").strip()
#     interests = (user_interest_text or "").strip()
#     kws = expand_keywords_with_llm(major, interests)

#     # 중복 제거, 순서 보존
#     seen, res = set(), []
#     for w in kws:
#         w = (w or "").strip()
#         if w and w not in seen:
#             seen.add(w)
#             res.append(w)
#     return res[:12]

# def expand_query_with_major(user_major: str, base_query: str) -> str:
#     kws = major_keywords(user_major, base_query)
#     return base_query + (" " + " ".join(kws) if kws else "")




# -*- coding: utf-8 -*-
# 기능: 전국대학별학과정보표준데이터에서 학과→관련직업을 수집하여
#       전공 인덱스를 만들고, 사용자 입력으로 전공을 해석/확장하는 RAG 진입점

from __future__ import annotations
import csv, re, os, json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import get_close_matches

STATUS_EXCLUDE = {"폐과"}  # 학과상태명에서 제외할 상태
KANON_FILE = "majors_jobs_map.json"

def _norm(s: str) -> str:
    s = re.sub(r"\(.*?\)", "", str(s))   # 괄호 내용 제거
    s = re.sub(r"\s+", "", s)            # 공백 제거
    s = s.replace("학과", "").replace("학부", "").replace("전공", "")
    return s.lower()

def _alias_set(name: str) -> List[str]:
    """전공명으로부터 흔한 변형 별칭 생성"""
    base = re.sub(r"\(.*?\)", "", name).strip()
    short = base.replace("학과","").replace("학부","").replace("전공","").strip()
    al = {base, short}
    # 간단 치환(예시 확장 가능)
    al |= {short.replace("국어국문", "국문"),
           short.replace("영어영문", "영문"),
           short.replace("컴퓨터공학", "컴퓨터"),
           short.replace("전자공학", "전자"),
           short.replace("기계공학", "기계"),
           short.replace("건축학", "건축")}
    return list({a for a in al if a})

@dataclass
class MajorEntry:
    name: str
    aliases: List[str]
    jobs: List[str]

def build_major_map(majors_csv: str, out_dir: str) -> str:
    """
    입력: 전국대학별학과정보표준데이터.csv (열: 학과명, 관련직업명, 학과상태명 ...)
    출력: taxonomy/majors_jobs_map.json
    """
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    # CP949 가능성 높음. 먼저 UTF-8, 안되면 CP949 순으로 시도.
    for enc in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
        try:
            with open(majors_csv, newline="", encoding=enc) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                break
        except Exception:
            continue
    else:
        raise RuntimeError("학과 CSV 인코딩을 해석할 수 없습니다.")

    major_map: Dict[str, MajorEntry] = {}
    # 컬럼 추출 유틸
    def pick(row: dict, *names: str) -> Optional[str]:
        for n in names:
            if n in row: return row[n]
        # 공백 제거 느슨매칭
        low = {k.replace(" ",""): k for k in row}
        for n in names:
            k = n.replace(" ","")
            if k in low: return row[low[k]]
        return None

    for r in rows:
        status = (pick(r, "학과상태명") or "").strip()
        if status and any(s in status for s in STATUS_EXCLUDE):
            continue
        name = (pick(r, "학과명") or "").strip()
        if not name or name in {"기타모집단위"}:
            continue
        jobs_raw = (pick(r, "관련직업명") or "").strip()
        jobs = []
        if jobs_raw:
            # '+' 구분(표준데이터 포맷)
            jobs = [j.strip() for j in re.split(r"[+/,;·∙•▶>-]+", jobs_raw) if j.strip()]

        key = _norm(name)  # 정규화 키
        if key not in major_map:
            major_map[key] = MajorEntry(name=name, aliases=_alias_set(name), jobs=[])
        major_map[key].jobs.extend(jobs)

    # 중복 제거/정돈
    for k, v in major_map.items():
        v.jobs = sorted(list({j for j in v.jobs if j}))

    out_path = out / KANON_FILE
    out_path.write_text(json.dumps({k: v.__dict__ for k,v in major_map.items()}, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out_path)

# def load_major_map(out_dir: str) -> Dict[str, MajorEntry]:
#     p = Path(out_dir) / KANON_FILE
#     if not p.exists():
#         return {}
#     raw = json.loads(p.read_text(encoding="utf-8"))
#     return {k: MajorEntry(**v) for k, v in raw.items()}
def load_major_map(out_dir: str) -> Dict[str, MajorEntry]:
    from pathlib import Path
    import json
    p = Path(out_dir) / "majors_jobs_map.json"
    if not p.exists():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    fixed: Dict[str, MajorEntry] = {}
    for k, v in raw.items():
        # 알 수 없는 키(courses 등) 무시, 기본값 보정
        name = v.get("name", "")
        aliases = v.get("aliases", []) or []
        jobs = v.get("jobs", []) or []
        fixed[k] = MajorEntry(name=name, aliases=aliases, jobs=jobs)
    return fixed

def resolve_major(user_text: str, major_map: Dict[str, MajorEntry]) -> Tuple[Optional[MajorEntry], List[str]]:
    """
    사용자 문장에서 전공 후보를 찾아 MajorEntry와 전공 키워드(job) 리스트를 돌려준다.
    못 찾으면 (None, []) 반환.
    """
    if not user_text:
        return None, []
    low = user_text.lower().strip()
    # 1) 정확/부분/별칭 매칭
    for k, v in major_map.items():
        # 원형/별칭 중 하나라도 포함되면 매칭
        names = [v.name] + v.aliases
        if any(n and n.lower() in low for n in names):
            return v, v.jobs

    # 2) 노말라이즈 후 근사 매칭
    norm_in = _norm(low)
    keys = list(major_map.keys())
    # difflib로 근사치(상위 1개) 찾기
    close = get_close_matches(norm_in, keys, n=1, cutoff=0.82)
    if close:
        m = major_map[close[0]]
        return m, m.jobs

    # 3) 실패 시 None
    return None, []

def expand_terms_for_major(user_text: str, major: Optional[MajorEntry], jobs: List[str], max_jobs: int = 18) -> List[str]:
    terms: List[str] = []
    if major:
        terms.append(major.name)
        terms.extend(major.aliases)
    terms.extend(jobs[:max_jobs])
    # 사용자 텍스트에서 의미있는 일반어 몇 가지 추출(간단)
    extras = [w for w in re.split(r"[^가-힣A-Za-z0-9]+", user_text) if 1 < len(w) <= 12]
    terms.extend(extras[:10])
    # 중복 제거
    seen = set(); out=[]
    for t in terms:
        t=t.strip()
        if t and t not in seen:
            seen.add(t); out.append(t)
    return out
