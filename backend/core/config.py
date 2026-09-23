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
