from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from pypdf import PdfReader
from db.mongo import db
from routes.auth_routes import router as auth_router
from routes.document_routes import router as document_router
from routes.analysis_routes import router as analysis_router
from routes.chat_routes import router as chat_router 
import time
import re

app = FastAPI(title="PDF Reader AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://project-716py.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'lar
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(analysis_router)
app.include_router(chat_router)

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# -------------------------
# Helpers
# -------------------------
def _safe_filename(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_").replace("\\", "_")


def normalize_extracted_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(
        r"(?:(?<=\s)|^)([A-Za-zÇĞİÖŞÜçğıöşü](?:\s+[A-Za-zÇĞİÖŞÜçğıöşü]){2,})(?=\s|$)",
        lambda m: m.group(1).replace(" ", ""),
        text,
    )

    text = re.sub(r"\s*@\s*", "@", text)
    text = re.sub(r"\s*\.\s*", ".", text)
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"\s*:\s*", ":", text)
    text = re.sub(r"(?<=\d)\s+(?=\d)", "", text)
    text = re.sub(r"\s*-\s*", " - ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = [line.strip() for line in text.split("\n")]
    cleaned_lines = []

    for line in lines:
        if not line:
            continue
        if len(line) == 1:
            continue

        line = re.sub(r"[|]{2,}", "|", line)
        line = re.sub(r"[_]{2,}", "_", line)
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines).strip()
    text = re.sub(r"[ ]{2,}", " ", text)

    return text


def extract_text_from_pdf(file_path: Path, max_pages: int = 20) -> str:
    reader = PdfReader(str(file_path))
    pages = reader.pages[:max_pages]

    parts = []
    for page in pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt)

    raw_text = "\n".join(parts).strip()
    cleaned_text = normalize_extracted_text(raw_text)
    return cleaned_text


def sentence_split(text: str) -> list[str]:
    if not text.strip():
        return []

    flat = re.sub(r"[ \t]+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", flat)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) < 3:
        line_parts = [ln.strip() for ln in text.split("\n") if ln.strip()]
        merged = []
        for ln in line_parts:
            ln = re.sub(r"\s+", " ", ln).strip()
            if len(ln) >= 20:
                merged.append(ln)
        if merged:
            parts = merged

    return parts


def score_summary_line(line: str) -> int:
    score = 0
    lower = line.lower()

    if len(line) >= 40:
        score += 2
    if len(line) >= 80:
        score += 2

    keywords = [
        "software", "engineer", "engineering", "student", "intern",
        "experience", "education", "summary", "skills", "project",
        "react", "node", "python", ".net", "java", "university",
        "istanbul", "developer"
    ]
    for kw in keywords:
        if kw in lower:
            score += 2

    digit_count = sum(ch.isdigit() for ch in line)
    if digit_count >= 8:
        score -= 2

    if "@" in line:
        score -= 2
    if "linkedin.com" in lower:
        score -= 2

    return score


def simple_summary(text: str, max_sentences: int = 5, max_chars: int = 900) -> str:
    if not text.strip():
        return "PDF içinden metin çıkarılamadı (muhtemelen taranmış görüntü/PDF)."

    parts = sentence_split(text)
    if not parts:
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned[:max_chars] + ("..." if len(cleaned) > max_chars else "")

    ranked = sorted(
        ((score_summary_line(p), idx, p) for idx, p in enumerate(parts)),
        key=lambda x: (-x[0], x[1])
    )

    selected = []
    used = set()

    for _, _, part in ranked:
        normalized = re.sub(r"\s+", " ", part).strip()

        if normalized in used:
            continue
        if len(normalized) < 25:
            continue
        if normalized.count("@") >= 1 and len(normalized) < 80:
            continue

        used.add(normalized)
        selected.append(normalized)

        if len(selected) >= max_sentences:
            break

    if not selected:
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned[:max_chars] + ("..." if len(cleaned) > max_chars else "")

    summary = " ".join(selected)
    summary = re.sub(r"\s+", " ", summary).strip()

    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "..."

    return summary


def luhn_check(number: str) -> bool:
    if not number.isdigit():
        return False

    total = 0
    reverse_digits = number[::-1]

    for i, d in enumerate(reverse_digits):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total % 10 == 0


def detect_sensitive(text: str):
    findings = []

    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if emails:
        uniq = sorted(set(emails))
        findings.append({
            "type": "email",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    phones = re.findall(r"(?:\+90|0)?5\d{9}", text)
    if phones:
        uniq = sorted(set(phones))
        findings.append({
            "type": "phone",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    tckn = re.findall(r"\b[1-9]\d{10}\b", text)
    if tckn:
        uniq = sorted(set(tckn))
        findings.append({
            "type": "tckn",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    ibans = re.findall(r"\bTR\d{24}\b", text, flags=re.IGNORECASE)
    if ibans:
        uniq = sorted(set(i.upper() for i in ibans))
        findings.append({
            "type": "iban",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    raw_cards = re.findall(r"\b(?:\d[ -]*?){13,19}\b", text)
    cleaned_cards = []

    phone_set = set(re.sub(r"\D", "", p) for p in phones) if phones else set()

    for candidate in raw_cards:
        digits = re.sub(r"\D", "", candidate)

        if not (13 <= len(digits) <= 19):
            continue
        if digits in phone_set:
            continue
        if re.fullmatch(r"(?:90)?5\d{9}", digits):
            continue
        if not luhn_check(digits):
            continue

        cleaned_cards.append(digits)

    if cleaned_cards:
        uniq = sorted(set(cleaned_cards))
        findings.append({
            "type": "card_number",
            "count": len(uniq),
            "samples": uniq[:5]
        })

    return findings


# -------------------------
# Models
# -------------------------
class FileReq(BaseModel):
    filename: str


# -------------------------
# Default endpoints
# -------------------------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type not in ["application/pdf", "application/octet-stream"]:
        return {"ok": False, "error": f"Only PDF allowed. Got: {file.content_type}"}

    ts = int(time.time())
    safe_name = _safe_filename(f"{ts}_{file.filename}")
    save_path = UPLOAD_DIR / safe_name

    content = await file.read()
    save_path.write_bytes(content)

    return {
        "ok": True,
        "filename": safe_name,
        "size": len(content),
        "content_type": file.content_type,
    }


@app.get("/files")
def list_files():
    files = sorted([p.name for p in UPLOAD_DIR.glob("*.pdf")])
    return {
        "ok": True,
        "count": len(files),
        "files": files
    }


@app.get("/files/{filename}")
def get_file(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@app.post("/summary")
def summary(req: FileReq):
    path = UPLOAD_DIR / req.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    text = extract_text_from_pdf(path, max_pages=20)
    summ = simple_summary(text, max_sentences=5, max_chars=900)

    return {
        "ok": True,
        "filename": req.filename,
        "text_len": len(text),
        "summary": summ,
    }


@app.post("/sensitive")
def sensitive(req: FileReq):
    path = UPLOAD_DIR / req.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    text = extract_text_from_pdf(path, max_pages=20)
    findings = detect_sensitive(text)

    return {
        "ok": True,
        "filename": req.filename,
        "text_len": len(text),
        "findings": findings,
    }


@app.post("/text-preview")
def text_preview(req: FileReq):
    path = UPLOAD_DIR / req.filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    text = extract_text_from_pdf(path, max_pages=20)

    return {
        "ok": True,
        "filename": req.filename,
        "text_len": len(text),
        "preview": text[:2000]
    }


@app.get("/db-check")
def db_check():
    try:
        result = db.command("ping")
        return {
            "ok": True,
            "database": db.name,
            "mongo_ping": result
        }
    except Exception as e:
        return {
            "ok": False,
            "database": db.name,
            "error": str(e)
        }