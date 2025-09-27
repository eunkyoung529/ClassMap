import re
from typing import Dict, List

PREF_PATTERNS = {
    "teamwork": [r"팀(플|프로젝트)", r"협업", r"코웍"],
    "coding": [r"코딩", r"개발", r"프로그래밍"],
    "design": [r"디자인", r"UI/?UX", r"프로토타입"],
    "data": [r"데이터", r"분석", r"머신러닝", r"AI"],
    "business": [r"창업", r"비즈니스", r"마케팅"]
}

def extract_preferences(text: str) -> List[str]:
    low = text.lower()
    prefs: List[str] = []
    for key, pats in PREF_PATTERNS.items():
        if any(re.search(p, low) for p in pats):
            prefs.append(key)
    return prefs

def score_by_preferences(text: str, prefs: List[str]) -> float:
    """아이템 설명에서 선호 키워드 등장 시 보너스(점수 감소)"""
    low = (text or "").lower()
    bonus = 1.0
    if "coding" in prefs and re.search(r"개발|코딩|프로그래밍", low): bonus *= 0.9
    if "teamwork" in prefs and re.search(r"팀|협업", low): bonus *= 0.92
    if "data" in prefs and re.search(r"데이터|머신러닝|ai", low): bonus *= 0.9
    if "design" in prefs and re.search(r"디자인|ui|ux|프로토타입", low): bonus *= 0.92
    if "business" in prefs and re.search(r"창업|비즈니스|마케팅", low): bonus *= 0.93
    return bonus
