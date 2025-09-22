# 기능 : (임시) CSV에서 공모전/대외활동 아이템 로딩.
# 나중에 Django/DB로 바꿔도 이 레이어만 교체하면 됨.

import csv
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Item:
    id: str
    type: str            # "contest" | "activity"
    title: str
    host: Optional[str]
    deadline: Optional[str]  # "YYYY-MM-DD" or None
    categories: List[str]
    link: Optional[str]
    description: Optional[str]
    target_majors: List[str]
    target_jobs: List[str]

def load_items_from_csv(path: str) -> list[Item]:
    items = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            items.append(Item(
                id=row.get("id") or str(i+1),
                type=row.get("type") or "contest",
                title=row.get("title") or row.get("제목") or "",
                host=row.get("host") or row.get("주최"),
                deadline=row.get("deadline") or row.get("마감일"),
                categories=[c.strip() for c in (row.get("categories") or row.get("분야") or "").split(",") if c.strip()],
                link=row.get("link") or row.get("링크"),
                description=row.get("description") or row.get("내용"),
                target_majors=[m.strip() for m in (row.get("target_majors") or "").split(",") if m.strip()],
                target_jobs=[j.strip() for j in (row.get("target_jobs") or "").split(",") if j.strip()],
            ))
    return items
