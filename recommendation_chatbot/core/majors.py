# 기능: 전국대학별학과정보표준데이터에서 학과→관련직업을 수집하여
#       전공 인덱스를 만들고, 사용자 입력으로 전공을 해석/확장하는 RAG 진입점

from __future__ import annotations
import csv, re, os, json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import get_close_matches

STATUS_EXCLUDE = {"폐과"}  
KANON_FILE = "majors_jobs_map.json"

def _norm(s: str) -> str:
    s = re.sub(r"\(.*?\)", "", str(s))   
    s = re.sub(r"\s+", "", s)           
    s = s.replace("학과", "").replace("학부", "").replace("전공", "")
    return s.lower()

def _alias_set(name: str) -> List[str]:
    """전공명으로부터 흔한 변형 별칭 생성"""
    base = re.sub(r"\(.*?\)", "", name).strip()
    short = base.replace("학과","").replace("학부","").replace("전공","").strip()
    al = {base, short}
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
            jobs = [j.strip() for j in re.split(r"[+/,;·∙•▶>-]+", jobs_raw) if j.strip()]

        key = _norm(name) 
        if key not in major_map:
            major_map[key] = MajorEntry(name=name, aliases=_alias_set(name), jobs=[])
        major_map[key].jobs.extend(jobs)

    # 중복 제거/정돈
    for k, v in major_map.items():
        v.jobs = sorted(list({j for j in v.jobs if j}))

    out_path = out / KANON_FILE
    out_path.write_text(json.dumps({k: v.__dict__ for k,v in major_map.items()}, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out_path)
def load_major_map(out_dir: str) -> Dict[str, MajorEntry]:
    from pathlib import Path
    import json
    p = Path(out_dir) / "majors_jobs_map.json"
    if not p.exists():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    fixed: Dict[str, MajorEntry] = {}
    for k, v in raw.items():
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
    for k, v in major_map.items():
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
