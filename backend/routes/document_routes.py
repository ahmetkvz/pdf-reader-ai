from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import Response
from pathlib import Path
import time
import base64

from db.mongo import documents_collection
from core.config import MAX_PDF_PAGES
from core.dependencies import get_current_user
from models.document_model import document_record
from services.rag_service import index_document
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
        .find({"userId": current_user["_id"]}, {"fileData": 0})
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
    file_data_b64 = ""
    page_count = None
    processed_pages = None

    if file.filename.lower().endswith(".pdf"):
        file_type = "pdf"
        text_content, processed_pages, page_count = extract_text_from_pdf(save_path, max_pages=MAX_PDF_PAGES)
        file_data_b64 = base64.b64encode(content).decode("utf-8")
    elif file.filename.lower().endswith(".txt"):
        file_type = "txt"
        text_content = content.decode("utf-8", errors="ignore")
    else:
        file_type = "unknown"

    document_type = detect_document_type(text_content, file.filename)

    doc = document_record(
        user_id=current_user["_id"],
        original_name=file.filename,
        stored_filename=safe_name,
        file_type=file_type,
        document_type=document_type,
        text_content=text_content,
        file_data=file_data_b64,
        page_count=page_count,
        processed_pages=processed_pages
    )

    result = documents_collection.insert_one(doc)

    if text_content.strip():
        index_document(str(result.inserted_id), text_content)

    truncated = page_count is not None and processed_pages < page_count
    warning = None
    if truncated:
        warning = (
            f"Belge {page_count} sayfa; sayfa sınırı nedeniyle yalnızca ilk "
            f"{processed_pages} sayfa işlendi. Analiz ve sohbet sonraki sayfaları kapsamaz."
        )

    return {
        "ok": True,
        "message": "Belge başarıyla yüklendi ve kaydedildi.",
        "documentId": str(result.inserted_id),
        "originalName": file.filename,
        "storedFilename": safe_name,
        "fileType": file_type,
        "documentType": document_type,
        "pageCount": page_count,
        "processedPages": processed_pages,
        "truncated": truncated,
        "warning": warning
    }


@router.get("/{document_id}/file")
def get_document_file(document_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId

    try:
        doc = documents_collection.find_one({
            "_id": ObjectId(document_id),
            "userId": current_user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz document id.")

    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")

    file_data_b64 = doc.get("fileData", "")
    if not file_data_b64:
        raise HTTPException(status_code=404, detail="Bu belge için dosya verisi bulunamadı.")

    file_bytes = base64.b64decode(file_data_b64)

    return Response(content=file_bytes, media_type="application/pdf")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    from bson import ObjectId
    from db.mongo import analyses_collection
    from pathlib import Path

    try:
        doc = documents_collection.find_one({
            "_id": ObjectId(document_id),
            "userId": current_user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz document id.")

    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")

    stored = doc.get("storedFilename")
    if stored:
        file_path = UPLOAD_DIR / stored
        if file_path.exists():
            file_path.unlink()

    documents_collection.delete_one({"_id": ObjectId(document_id)})
    analyses_collection.delete_many({"documentId": document_id})

    return {"ok": True, "message": "Belge silindi."}
