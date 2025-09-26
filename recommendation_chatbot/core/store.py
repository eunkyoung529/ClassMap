from __future__ import annotations
import csv
import hashlib
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class Item:
    id: str
    type: str                 # "contest" | "activity"
    title: str
    host: Optional[str]
    deadline: Optional[str]
    categories: List[str]
    target_jobs: List[str]
    target_majors: List[str]
    link: Optional[str]
    description: Optional[str]
    rating: Optional[float]

def _make_id(title: str, link: Optional[str]) -> str:
    base = (title or "") + "|" + (link or "")
    return hashlib.md5(base.encode("utf-8")).hexdigest()

def _split_categories(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"[,\|/;·∙•▶>\-]+", raw)]
    return [p for p in parts if p]

# ---- 인코딩 + 구분자 자동 감지 ----
def _open_sniffed_reader(path: str) -> Tuple[object, csv.DictReader]:
    encodings = ("utf-8", "utf-8-sig", "cp949", "euc-kr")
    for enc in encodings:
        try:
            f = open(path, "r", encoding=enc, newline="")
            # 샘플로 dialect 추론
            sample = f.read(8192)
            if not sample:
                f.close()
                continue
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except Exception:
                # 기본은 콤마로
                class _D(csv.Dialect):
                    delimiter = ","
                    quotechar = '"'
                    doublequote = True
                    skipinitialspace = True
                    lineterminator = "\n"
                    quoting = csv.QUOTE_MINIMAL
                dialect = _D()
            reader = csv.DictReader(f, dialect=dialect)
            if reader.fieldnames:
                return f, reader
            f.close()
        except UnicodeDecodeError:
            continue
        except Exception:
            # 다른 오류면 다음 인코딩 시도
            continue
    raise RuntimeError(f"CSV 인코딩/구분자를 해석하지 못했습니다: {path}")

def _normalize_header(h: str) -> str:
    return (h or "").replace("\ufeff", "").strip()

def _build_cols_map(fieldnames: List[str]) -> Dict[str, str]:
    cols = {}
    for c in fieldnames or []:
        cols[_normalize_header(c)] = c
    return cols

def _pick_column(cols: Dict[str, str], *cands: str) -> Optional[str]:
    # 1) 원문
    for c in cands:
        if c in cols:
            return cols[c]
    # 2) 공백 제거
    compact = {k.replace(" ", ""): v for k, v in cols.items()}
    for c in cands:
        k = c.replace(" ", "")
        if k in compact:
            return compact[k]
    # 3) 소문자
    lower = {k.lower(): v for k, v in cols.items()}
    for c in cands:
        k = c.lower()
        if k in lower:
            return lower[k]
    return None

def load_items_from_csv(csv_path: str) -> List[Item]:
    items: List[Item] = []

    f, reader = _open_sniffed_reader(csv_path)
    with f:
        cols = _build_cols_map(reader.fieldnames or [])

        col_title = _pick_column(cols, "제목", "공모전명", "타이틀", "title", "Title", "명칭", "대회명")
        col_host  = _pick_column(cols, "주최", "주관", "host", "Host", "Organizer", "기관명", "기관")
        col_dead  = _pick_column(cols, "마감일", "접수마감", "deadline", "마감", "Deadline", "Due", "접수기간", "마감기한")
        col_cats  = _pick_column(cols, "분야", "카테고리", "분류", "category", "Categories", "영역", "분야명")
        col_link  = _pick_column(cols, "링크", "URL", "url", "link", "Link", "홈페이지", "접수링크")
        col_desc  = _pick_column(cols, "내용", "설명", "요약", "본문", "description", "Description", "Summary", "개요")

        for row in reader:
            # DictReader가 None을 줄 수 있으니 안전하게 처리
            get = lambda k: (row.get(k) if k else "") or ""

            title = get(col_title).strip()
            if not title:
                continue

            host = get(col_host).strip() or None
            dead = get(col_dead).strip() or None
            cats = _split_categories(get(col_cats).strip()) if col_cats else []
            link = get(col_link).strip() or None
            desc = get(col_desc).strip() or None

            items.append(Item(
                id=_make_id(title, link),
                type="contest",
                title=title,
                host=host,
                deadline=dead,
                categories=cats,
                target_jobs=[],
                target_majors=[],
                link=link,
                description=desc,
                rating=None,
            ))

    return items

def merge_ratings(items: List[Item], ratings_csv: str) -> None:
    rmap: Dict[str, float] = {}
    try:
        f, reader = _open_sniffed_reader(ratings_csv)
    except Exception:
        return
    with f:
        for row in reader:
            t = ((row.get("title") or row.get("제목") or "").strip())
            if not t:
                continue
            r = (row.get("rating") or row.get("평점") or "").strip()
            if not r:
                continue
            try:
                rmap[t] = float(r)
            except ValueError:
                continue

    if not rmap:
        return

    for it in items:
        if it.title in rmap and it.rating is None:
            it.rating = rmap[it.title]