import json, uuid

def split_with_overlap(text, max_chunk_size=500, overlap=50):
    """
    텍스트를 중첩(overlap)을 두고 청크로 분리합니다.
    """
    chunks, start = [], 0
    while start < len(text):
        end = start + max_chunk_size
        chunks.append(text[start:end])
        start += max_chunk_size - overlap
    return chunks

def chunk_courses(input_jsonl, output_jsonl, max_chunk_size=500, overlap=50):
    """
    강의계획서 JSONL 파일을 읽어 부모-자식 청크로 분리하여 저장합니다.
    """
    with open(input_jsonl, "r", encoding="utf-8") as fin, \
         open(output_jsonl, "w", encoding="utf-8") as fout:
        for line in fin:
            course = json.loads(line.strip())

        
            course_id = course.get("course_id") or str(uuid.uuid4())
            title = course.get("title", "알수없는과목")
            instructor = course.get("instructor") or course.get("professor")
            
            meta = {
                "course_id": course_id,
                "course_code": course.get("course_code"),
                "title": title,
                "department": course.get("department"),
                "course_type": course.get("course_type"),
                "professor": instructor,
                "time": course.get("schedule") or course.get("time"),
                "target": course.get("target"),
                "credits": course.get("credits"),
                "hours": course.get("hours"),
                "email": course.get("email"),
            }

        
            parent_id = str(uuid.uuid4())
            parent_chunk = {
                "chunk_id": parent_id,
                "parent_id": None,
                "chunk_type": "parent",
                **meta,
                "text": "\n".join([
                    f"강의명: {title}",
                    f"교수명: {instructor}",
                    f"[개요] {course.get('overview','')}",
                    f"[수업목표] {course.get('objectives','')}",
                    f"[평가방식] {course.get('evaluation','')}",
                    f"[교재] {course.get('textbook','')}"
                ])
            }
            fout.write(json.dumps(parent_chunk, ensure_ascii=False) + "\n")

         
            for idx, week_text in enumerate(course.get("weekly_plan", []), start=1):
                week_label = f"{idx}주차"
                chunks = split_with_overlap(week_text, max_chunk_size, overlap=overlap)
                base_id = str(uuid.uuid4())
                for sub_idx, chunk in enumerate(chunks, start=1):
                    child_chunk = {
                        "chunk_id": f"{base_id}_{sub_idx}",
                        "parent_id": parent_id,
                        "chunk_type": "weekly",
                        "week": week_label,
                        **meta,
                        "text": chunk.strip()
                    }
                    fout.write(json.dumps(child_chunk, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    input_jsonl = "syllabus_all.jsonl"
    output_jsonl = "syllabus_chunks.jsonl"
    chunk_courses(input_jsonl, output_jsonl, max_chunk_size=500, overlap=50)
    print(f"부모-자식 청킹 완료: {output_jsonl}")
