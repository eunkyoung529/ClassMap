# import pandas as pd
# import re
# from .config import MAJORS_CSV

# # 전공→도메인 키워드 사전(핵심 키워드만; 필요시 확장)
# DOMAIN_KWS = {
#     "컴퓨터|소프트|정보통신|전자계산": ["개발","프로그래밍","AI","데이터","알고리즘","보안","해커톤","웹","백엔드","프론트엔드","클라우드"],
#     "경제|경영|무역|회계|금융|통계": ["데이터분석","데이터","파이썬","통계","모델링","경진대회","핀테크","스타트업","마케팅"],
#     "건축|도시|조경|인테리어": ["건축설계","BIM","CAD","모델링","공모전","디자인","스마트시티","친환경"],
#     "전기|전자|제어|반도체": ["임베디드","IoT","로봇","펌웨어","에너지","회로","전력","자율주행"],
#     "기계|메카트로닉스|항공|조선": ["로봇","CAD","시뮬레이션","제조","자율주행","드론"],
#     "화학|신소재|재료|바이오|생명": ["신소재","공정","실험","분석","바이오","의료AI","환경"],
#     "디자인|시각|산업디자인|미디어": ["UI","UX","그래픽","브랜딩","프로토타이핑","인터랙션","웹디자인"],
#     "수학|물리|통계": ["데이터","모델링","최적화","시뮬레이션","수리통계"],
#     "문학|사회|행정|정치|법학": ["정책","공공데이터","데이터분석","리서치","캠페인","커뮤니케이션"],
# }

# def load_majors() -> pd.DataFrame:
#     try:
#         df = pd.read_csv(MAJORS_CSV, encoding="utf-8")
#     except UnicodeDecodeError:
#         df = pd.read_csv(MAJORS_CSV, encoding="cp949")
#     cols = df.columns.tolist()
#     cand = [c for c in cols if any(k in c for k in ["학과","전공","학부","계열","과(학과)"])]
#     name_col = cand[0] if cand else cols[0]
#     out = pd.DataFrame()
#     out["name"] = df[name_col].astype(str).fillna("")
#     out["norm"] = out["name"].str.replace(r"\s+", "", regex=True).str.lower()
#     return out.drop_duplicates("norm").reset_index(drop=True)

# def expand_query_with_major(user_major: str, base_query: str) -> str:
#     mj = (user_major or "").replace(" ", "").lower()
#     # 사전 매칭
#     add = []
#     for pattern, kws in DOMAIN_KWS.items():
#         if re.search(pattern, user_major):
#             add.extend(kws)
#     if add:
#         return base_query + " " + " ".join(sorted(set(add)))
#     # 사전에 없으면 그대로
#     return base_query







# import pandas as pd
# import re
# from pathlib import Path
# from .config import MAJORS_CSV

# def _read_table(path: str) -> pd.DataFrame:
#     p = Path(path)
#     # 1) 확장자 기준
#     if p.suffix.lower() in [".xlsx", ".xls"]:
#         try:
#             return pd.read_excel(path, engine="openpyxl" if p.suffix.lower()==".xlsx" else None)
#         except Exception:
#             # openpyxl 미설치 시: pip install openpyxl
#             raise

#     # 2) CSV 시도(여러 인코딩)
#     for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
#         try:
#             return pd.read_csv(path, encoding=enc)
#         except Exception:
#             pass

#     # 3) 확장자가 .csv여도 실제 엑셀인 경우를 마지막으로 시도
#     try:
#         return pd.read_excel(path, engine="openpyxl")
#     except Exception:
#         raise RuntimeError(
#             "전공 파일을 읽을 수 없습니다. 엑셀(.xlsx)로 저장하거나 CSV UTF-8로 다시 저장해 주세요."
#         )

# def load_majors() -> pd.DataFrame:
#     df = _read_table(MAJORS_CSV)
#     cols = df.columns.tolist()
#     # 전공명으로 보이는 컬럼 탐색
#     cand = [c for c in cols if any(k in str(c) for k in ["학과","전공","학부","계열","과(학과)","학과명","학과(전공)"])]
#     name_col = cand[0] if cand else cols[0]
#     out = pd.DataFrame()
#     out["name"] = df[name_col].astype(str).fillna("")
#     out["norm"] = out["name"].str.replace(r"\s+", "", regex=True).str.lower()
#     return out.drop_duplicates("norm").reset_index(drop=True)

# # --- 아래 두 함수가 기존 코드와 연결됩니다 ---
# def major_keywords(user_major: str, user_interest_text: str = "") -> list[str]:
#     # LLM 기반 확장(기존 llm.expand_keywords_with_llm 사용)
#     from .llm import expand_keywords_with_llm
#     key = f"{(user_major or '').strip()}|{(user_interest_text or '').strip()}"
#     kws = expand_keywords_with_llm(user_major, user_interest_text)
#     # 중복 제거
#     seen=set(); res=[]
#     for w in kws:
#         if w and w not in seen:
#             seen.add(w); res.append(w)
#     return res[:12]

# def expand_query_with_major(user_major: str, base_query: str) -> str:
#     kws = major_keywords(user_major, base_query)
#     return base_query + (" " + " ".join(kws) if kws else "")



import os
import re
from pathlib import Path
import pandas as pd
from .config import MAJORS_CSV

# 환경변수로 특정 시트/컬럼을 지정할 수 있습니다(엑셀일 때 유용)
ENV_SHEET = os.environ.get("RC_MAJORS_SHEET", "").strip()
ENV_COL   = os.environ.get("RC_MAJORS_COL", "").strip()

STATUS_WORDS = {"기존", "폐과", "신설", "변경", "통합", "비고", "상태", "구분"}

# -----------------------------
# 내부: 전공 테이블 읽기 (CSV/엑셀 자동 판별)
# -----------------------------
def _read_table_any(path: str) -> dict[str, pd.DataFrame]:
    """
    엑셀(.xlsx/.xls)은 모든 시트를 dict로, CSV는 단일 시트를 dict로 반환.
    반환 형태: {'sheetname': df}
    """
    p = Path(path)
    if p.suffix.lower() in [".xlsx", ".xls"]:
        if ENV_SHEET:
            df = pd.read_excel(path, sheet_name=ENV_SHEET, engine="openpyxl" if p.suffix.lower()==".xlsx" else None)
            return {ENV_SHEET: df}
        dfs = pd.read_excel(path, sheet_name=None, engine="openpyxl" if p.suffix.lower()==".xlsx" else None)
        return {str(k): v for k, v in dfs.items()}

    # CSV: 여러 인코딩 시도
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(path, encoding=enc)
            return {"csv": df}
        except Exception:
            continue

    # CSV 확장자지만 실은 엑셀 바이너리인 경우 마지막 시도
    try:
        df = pd.read_excel(path, engine="openpyxl")
        return {"excel_from_csv": df}
    except Exception as e:
        raise RuntimeError(f"전공 파일을 읽을 수 없습니다: {path}\n{e}")

def _korean_ratio(s: str) -> float:
    if not isinstance(s, str) or not s:
        return 0.0
    total = len(s)
    kor = sum(1 for ch in s if '\uac00' <= ch <= '\ud7a3')
    return kor / total if total else 0.0

def _score_column(series: pd.Series) -> float:
    """
    전공명일 가능성 점수: 한글 비율, 유일값 수, 평균 길이 등으로 휴리스틱 스코어 계산
    """
    try:
        s = series.dropna().astype(str).head(200)
    except Exception:
        return -1e9
    if s.empty:
        return -1e9

    uniq = s.unique()
    uniq_count = len(uniq)
    avg_len = s.map(len).mean()
    kor_ratio = s.map(_korean_ratio).mean()
    status_hits = sum(1 for v in uniq if str(v).strip() in STATUS_WORDS)
    status_penalty = status_hits / max(1, uniq_count)

    score = (
        kor_ratio * 3.0
        + (min(uniq_count, 200) / 200.0) * 2.0
        + (min(avg_len, 12) / 12.0) * 1.0
        - status_penalty * 2.5
    )
    return float(score)

def _choose_major_column(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    # 1) 환경변수 우선
    if ENV_COL and ENV_COL in cols:
        return ENV_COL
    # 2) 컬럼명 키워드 매칭 우선
    preferred = [c for c in cols if any(k in str(c) for k in ["학과","전공","학부","계열","과(학과)","학과명","학과(전공)"])]
    if preferred:
        return preferred[0]
    # 3) 점수 기반 탐색
    scored = sorted(((c, _score_column(df[c])) for c in cols), key=lambda x: x[1], reverse=True)
    return scored[0][0]

# -----------------------------
# 공개 API
# -----------------------------
def load_majors() -> pd.DataFrame:
    """
    majors.csv/xlsx를 읽어 전공명 테이블 반환: columns = [name, norm]
    """
    tables = _read_table_any(MAJORS_CSV)
    best_df = None; best_col = None; best_score = -1e9

    for _, df in tables.items():
        if df is None or df.empty:
            continue
        try:
            col = _choose_major_column(df)
            score = _score_column(df[col])
            if score > best_score:
                best_score = score
                best_df = df
                best_col = col
        except Exception:
            continue

    if best_df is None:
        raise RuntimeError("학과(전공) 컬럼을 자동 탐지하지 못했습니다. .env의 RC_MAJORS_SHEET/RC_MAJORS_COL을 지정하세요.")

    s = best_df[best_col].astype(str).fillna("")
    # 불필요한 상태 단어 제거 + 공백행 제거
    s = s[~s.str.strip().isin(STATUS_WORDS)]
    s = s[s.str.strip() != ""]

    out = pd.DataFrame()
    out["name"] = s
    out["norm"] = out["name"].str.replace(r"\s+", "", regex=True).str.lower()
    out = out.drop_duplicates("norm").reset_index(drop=True)
    return out

def major_keywords(user_major: str, user_interest_text: str = "") -> list[str]:
    """
    전공명 + (선택)사용자 취향문장 -> LLM이 키워드 자동 생성.
    순환 임포트를 피하기 위해 여기서 지연 임포트 합니다.
    """
    # 지연 임포트(순환 방지)
    from .llm import expand_keywords_with_llm

    major = (user_major or "").strip()
    interests = (user_interest_text or "").strip()
    kws = expand_keywords_with_llm(major, interests)

    # 중복 제거, 순서 보존
    seen, res = set(), []
    for w in kws:
        w = (w or "").strip()
        if w and w not in seen:
            seen.add(w)
            res.append(w)
    return res[:12]

def expand_query_with_major(user_major: str, base_query: str) -> str:
    kws = major_keywords(user_major, base_query)
    return base_query + (" " + " ".join(kws) if kws else "")

