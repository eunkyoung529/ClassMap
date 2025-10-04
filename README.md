# ClassMap

```
## **1. 커밋 컨벤션**

커밋 메시지는 다음 규칙을 따릅니다:

```
[타입] 모듈명: 메시지 내용
```

- **타입** (소문자):
    - feat: 새로운 기능 추가
    - fix: 버그 수정
    - docs: 문서 수정
    - style: 코드 포맷팅, 세미콜론 누락 등 (코드 변경 없음)
    - refactor: 리팩토링 (기능 추가/변경 없음)
    - test: 테스트 코드 추가/수정
    - chore: 빌드 작업, 의존성 관리 등 기타 작업

예시:

```
feat member: 회원 가입 기능 구현
fix auth: 로그인 시 인증 오류 수정
```



실행방법


1. .env에 azure api 키 입력
2. (jsonl 파일이 없다는 가정하에) loader and chunking에 있는 파일 다 돌리기
3. jsonl 파일 두개 생성되면 아래 명령어 터미널에 입력
실행 명령어: python -m chatbot.rag_chatbot --chunks syllabus_chunks.jsonl --query "나는 디지털소프트웨어공학부 학생인데 컴퓨터비전 강의 추천해줘" --chat

