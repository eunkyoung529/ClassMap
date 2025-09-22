# 기능 : 학과 CSV로 학과↔직무 사전 생성/저장, 로딩, 질의어 확장.
import json, re
from pathlib import Path
import pandas as pd

def _norm(s: str) -> str:
    return re.sub(r"\s+", "", str(s)).lower()

def build_major_map(csv_path: str, out_dir: str) -> str:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="cp949")

    major_map = {}
    for _, r in df.iterrows():
        major = str(r.get("학과명", "")).strip()
        if not major:
            continue
        jobs = [x.strip() for x in str(r.get("관련직업명", "")).split(",") if x and x != "nan"]
        courses = [x.strip() for x in str(r.get("주요교과목명", "")).split(",") if x and x != "nan"]

        key = _norm(major)
        bucket = major_map.setdefault(key, {"name": major, "aliases": set(), "jobs": set(), "courses": set()})
        bucket["jobs"].update(jobs); bucket["courses"].update(courses)

    # 간단 별칭 규칙(필요시 추가)
    for v in major_map.values():
        name = v["name"]
        if "컴퓨터" in name or "소프트웨어" in name: v["aliases"].update({"컴공","소프트웨어","CS"})
        if "전자" in name: v["aliases"].add("전자과")

    # set → list
    for v in major_map.values():
        v["aliases"] = list(v["aliases"])
        v["jobs"] = list(v["jobs"])
        v["courses"] = list(v["courses"])

    out_path = out / "majors_jobs_map.json"
    out_path.write_text(json.dumps(major_map, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out_path)

def load_major_map(out_dir: str) -> dict:
    p = Path(out_dir) / "majors_jobs_map.json"
    if not p.exists(): return {}
    return json.loads(p.read_text(encoding="utf-8"))

def expand_query_with_taxonomy(query: str, tax: dict) -> list[str]:
    low = query.lower()
    terms = {query}
    for v in tax.values():
        names = [v["name"]] + v["aliases"]
        if any(n.lower() in low for n in names):
            terms.update([v["name"], *v["aliases"], *v["jobs"]])
    return list(terms)
