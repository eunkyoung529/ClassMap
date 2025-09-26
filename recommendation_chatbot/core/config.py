# import os
# from pathlib import Path
# from dotenv import load_dotenv

# # .env 로드
# ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
# if ENV_PATH.exists():
#     load_dotenv(ENV_PATH.as_posix())

# BASE_PATH = Path(__file__).resolve().parents[1]
# DATA_DIR = BASE_PATH / "data"
# VECTOR_DIR = DATA_DIR / "vector_index"

# # 파일 경로
# CONTESTS_CSV = os.environ.get("RC_CONTESTS_CSV", (BASE_PATH / "공모전_200개.csv").as_posix())
# MAJORS_CSV   = os.environ.get("RC_MAJORS_CSV", (DATA_DIR / "majors.csv").as_posix())
# INDEX_PKL    = (VECTOR_DIR / "index.pkl").as_posix()

# # Azure OpenAI
# AZURE_OPENAI_KEY         = os.environ.get("AZURE_OPENAI_KEY", "")
# AZURE_OPENAI_ENDPOINT    = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
# AZURE_OPENAI_DEPLOYMENT  = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
# AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

# TOP_K = int(os.environ.get("RC_TOP_K", "6"))
# MAX_CTX = int(os.environ.get("RC_MAX_CTX", "6"))  # LLM prompt에 넣는 문서 수
