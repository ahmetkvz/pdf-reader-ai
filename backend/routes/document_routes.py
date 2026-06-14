from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pathlib import Path
import time

from db.mongo import documents_collection
from core.dependencies import get_current_user
from models.document_model import document_record
from services.pdf_service import extract_text_from_pdf
from services.analysis_service import detect_document_type

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def _safe_filename(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_").replace("\\", "_")


@router.get("/me")
def get_my_documents(current_user: dict = Depends(get_current_user)):
    docs = list(
        documents_collection
        .find({"userId": current_user["_id"]})
        .sort("uploadDate", -1)
    )

    for doc in docs:
        doc["_id"] = str(doc["_id"])

    return {
        "ok": True,
        "count": len(docs),
        "documents": docs
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if file.content_type not in ["application/pdf", "application/octet-stream", "text/plain"]:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya türü: {file.content_type}"
        )

    ts = int(time.time())
    safe_name = _safe_filename(f"{ts}_{file.filename}")
    save_path = UPLOAD_DIR / safe_name

    content = await file.read()
    save_path.write_bytes(content)

    file_type = "unknown"
    text_content = ""

    if file.filename.lower().endswith(".pdf"):
        file_type = "pdf"
        text_content = extract_text_from_pdf(save_path, max_pages=20)

    elif file.filename.lower().endswith(".txt"):
        file_type = "txt"
        text_content = content.decode("utf-8", errors="ignore")

    else:
        file_type = "unknown"

    # ÖNEMLİ:
    # Belge türü tespiti PDF/TXT ayrımından sonra yapılmalı.
    # Böylece PDF veya TXT dosyalarında da çalışır.
    document_type = detect_document_type(text_content, file.filename)


    doc = document_record(
        user_id=current_user["_id"],
        original_name=file.filename,
        stored_filename=safe_name,
        file_type=file_type,
        document_type=document_type,
        text_content=text_content
    )

    result = documents_collection.insert_one(doc)

    return {
        "ok": True,
        "message": "Belge başarıyla yüklendi ve kaydedildi.",
        "documentId": str(result.inserted_id),
        "originalName": file.filename,
        "storedFilename": safe_name,
        "fileType": file_type,
        "documentType": document_type
    }