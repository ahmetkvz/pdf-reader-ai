import os
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} ortam değişkeni tanımlı değil. "
            f"Lütfen backend/.env dosyasına {name} değerini ekleyin."
        )
    return value


MONGO_URI = _require_env("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "pdf_reader_ai")

JWT_SECRET = _require_env("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "500"))
CHAT_MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "1000"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))

# S3 uyumlu nesne depolama (Cloudflare R2 vb.). Eksikse uygulama açılır ama PDF yüklenemez.
STORAGE_ENDPOINT_URL = os.getenv("STORAGE_ENDPOINT_URL") or None
STORAGE_ACCESS_KEY_ID = os.getenv("STORAGE_ACCESS_KEY_ID") or None
STORAGE_SECRET_ACCESS_KEY = os.getenv("STORAGE_SECRET_ACCESS_KEY") or None
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET") or None
