# 기능 : (임시) CSV에서 공모전/대외활동 아이템 로딩.
# 나중에 Django/DB로 바꿔도 이 레이어만 교체하면 됨.
# + 별점까지 추가함

import pandas as pd
from dateutil import parser
from .config import CONTESTS_CSV

COLUMN_MAP = {
    "제목": "title",
    "주최": "host",
    "마감일": "deadline",
    "분야": "field",
    "링크": "link",
    "내용": "content",
}

def _norm(s: str) -> str:
    if pd.isna(s): return ""
    return " ".join(str(s).strip().split())

def _parse_deadline(x: str):
    x = _norm(x)
    if not x: return None
    if any(k in x for k in ["상시", "미정", "수시", "~"]): return None
    try:
        d = parser.parse(x, dayfirst=False, yearfirst=True).date()
        return d.isoformat()
    except Exception:
        return None

def load_contests(path: str | None = None) -> pd.DataFrame:
    csv_path = path or CONTESTS_CSV
    df = pd.read_csv(csv_path, encoding="utf-8")
    df = df.rename(columns={c: COLUMN_MAP.get(c, c) for c in df.columns})
    for c in ["title","host","deadline","field","link","content"]:
        if c not in df.columns: df[c] = ""
        df[c] = df[c].apply(_norm)
    df["deadline"] = df["deadline"].apply(_parse_deadline)

    # 가중치가 반영된 검색 텍스트: title*2 + field*1.5 + content + host
    df["text"] = (
        (df["title"].fillna("") + " ") * 2
        + (df["field"].fillna("") + " ") * 1
        + df["content"].fillna("") + " "
        + df["host"].fillna("")
    ).str.lower()

    return df



