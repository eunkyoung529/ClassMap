import re
import unicodedata

BASIC_KWS = [
    # 데이터/AI
    "데이터분석","데이터","ai","인공지능","머신러닝","딥러닝","통계","모델링","공공데이터",
    # 개발
    "개발","프로그래밍","백엔드","프론트엔드","웹","앱","api","해커톤","보안","클라우드","iot","임베디드",
    # 건축/도시/환경
    "bim","cad","스마트시티","친환경","환경","도시계획","도시재생","제로에너지",
    # 디자인/콘텐츠
    "ui","ux","그래픽","브랜딩","프로토타입","인터랙션","콘텐츠","게임",
]

def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()

def extract_interests(user_text: str) -> list[str]:
    txt = normalize_text(user_text).lower()
    found = [w for w in BASIC_KWS if w.lower() in txt]
    # 추가: 간단 토큰 추출
    if not found:
        cand = re.findall(r"[가-힣A-Za-z0-9+#]+", txt)
        found = [t for t in cand if len(t) >= 2]
    seen=set(); out=[]
    for w in found:
        if w not in seen:
            seen.add(w); out.append(w)
    return out[:12]  # 과도 확장 방지
