import os
import json
import pdfplumber
import re

# PDF 상단/하단 정보 제거를 위한 정규식
HEADER_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}")
HEADER_PAGE = re.compile(r"^\d+/\d+")

def extract_text_from_pdf(pdf_path):
    """PDF에서 텍스트 추출 (상단/하단의 다운로드 사용자/시간/페이지 정보 제거)"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            cleaned = []
            for line in page_text.splitlines():
                if HEADER_DATE.search(line):
                    continue
                if HEADER_PAGE.match(line.strip()):
                    continue
                cleaned.append(line)
            text += "\n".join(cleaned) + "\n"
    return text

def parse_first_group(pattern, text, flags=0, default=None):
    """주어진 패턴으로 텍스트에서 첫 번째 그룹을 추출"""
    m = re.search(pattern, text, flags)
    return (m.group(1).strip() if m and m.lastindex else (m.group(0).strip() if m else default))

def extract_instructor(text):
    """'담당교수' 줄 근처에서 '성명: OOO' 패턴을 찾아 교수명 추출"""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "담당교수" in line.replace(" ", ""):
            for j in range(i + 1, min(i + 8, len(lines))):
                m = re.search(r"성명\s*[:：]\s*([^\s]+)", lines[j])
                if m:
                    return m.group(1).strip()
    m = re.search(r"성명\s*[:：]\s*([^\s]+)", text)
    return m.group(1).strip() if m else None

def split_category_line(raw_category):
    """'이수구분' 줄에서 과목 유형, 시간, 수강대상 추출"""
    course_type = None
    schedule = None
    target = None
    if raw_category:
        if "전공" in raw_category:
            course_type = "전공"
        elif "교양" in raw_category:
            course_type = "교양"

        sch_m = re.search(r"수업시간\s*([^\n]+)", raw_category)
        if sch_m:
            schedule = re.sub(r"\s*수강대상.*$", "", sch_m.group(1)).strip()

        tgt_m = re.search(r"수강대상\s*([^\n]+)", raw_category)
        if tgt_m:
            target = tgt_m.group(1).strip()
    return course_type, schedule, target

def normalize_course(text, department=None):
    """강의계획서 텍스트에서 추천용 JSON 구조 생성"""
    raw_category = parse_first_group(r"이수구분\s*\n?([^\n]+)", text)
    course_type, schedule, target = split_category_line(raw_category)

    # 섹션 제목을 기반으로 각 필드 내용 추출
    overview = parse_first_group(r"교과목 개요\s*(.*?)II", text, flags=re.S)
    objectives = parse_first_group(r"수업목표.*?핵심\s*역량.*?\n(.*?)III", text, flags=re.S)
    evaluation = parse_first_group(r"학습평가방식\s*(.*?)Ⅶ", text, flags=re.S)
    textbook = parse_first_group(r"교재 및 참고문헌\s*(.*?)(?:X|XI)", text, flags=re.S)
    
    # weekly_plan을 더 유연하게 추출
    weekly_plan_text = parse_first_group(r"X\. 주차별 수업계획\s*(.*?)XI", text, flags=re.S)
    weekly_plan = []
    if weekly_plan_text:
        # 각 "주차" 블록을 찾고 내용을 저장
        weeks = re.split(r"\d+\s*주차", weekly_plan_text)
        # 첫 번째 항목은 비어있을 수 있으므로 건너뜀
        for content in weeks[1:]:
            # 공백, 줄바꿈 제거 후 내용만 남김
            cleaned_content = content.replace("수업활동", "").strip()
            if cleaned_content:
                weekly_plan.append(cleaned_content)

    course = {
        "course_id": parse_first_group(r"(\d{6})\s*학점", text),
        "title": re.sub(r"\s*과목코드.*", "", parse_first_group(r"과목명\s*\n?([^\n]+)", text)),
        "course_code": parse_first_group(r"과목코드\s*(\d+)", text),
        "hours": parse_first_group(r"\d+/\d+", text),
        "department": department,
        "course_type": course_type,
        "credits": parse_first_group(r"(\d+)\s*/\s*\d+", text),
        "target": target,
        "instructor": extract_instructor(text),
        "email": parse_first_group(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text),
        "schedule": schedule,
        "language": "한국어",
        "skills": [],
        "tags": [course_type] if course_type else [],
        "difficulty": "입문" if ("기초" in text or "입문" in text) else "중급",
        "teaching_method": re.findall(r"(강의|실험/실습|프로젝트|토론|발표)", text),
        "overview": overview,
        "objectives": objectives,
        "evaluation": evaluation,
        "textbook": textbook,
        "weekly_plan": weekly_plan,
    }
    return course

def process_all_pdfs(root_folder, output_jsonl):
    """폴더 내 모든 PDF 처리 후 JSONL 저장"""
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for dirpath, _, filenames in os.walk(root_folder):
            department = os.path.basename(dirpath)
            for file_name in filenames:
                if not file_name.lower().endswith(".pdf"):
                    continue
                pdf_path = os.path.join(dirpath, file_name)
                print(f"Processing {pdf_path} ...")
                try:
                    text = extract_text_from_pdf(pdf_path)
                    course_data = normalize_course(text, department=department)
                    f.write(json.dumps(course_data, ensure_ascii=False) + "\n")
                except Exception as e:
                    print(f"Error processing {pdf_path}: {e}")

if __name__ == "__main__":
    root_folder = "./강의계획서 자료"
    output_jsonl = "syllabus_all.jsonl"
    process_all_pdfs(root_folder, output_jsonl)
    print(f"JSONL 생성 완료: {output_jsonl}")