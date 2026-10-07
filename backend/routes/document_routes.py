from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import Response
from bson import ObjectId
import base64
import logging
import uuid

from db.mongo import documents_collection, analyses_collection, notes_collection
from core.config import MAX_PDF_PAGES, MAX_UPLOAD_MB
from core.dependencies import get_current_user
from models.document_model import document_record
from services.rag_service import index_document
from services.pdf_service import extract_text_from_pdf
from services.analysis_service import detect_document_type
from services import storage_service
from services.storage_service import StorageError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


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

    # Dosyanın tamamını belleğe almadan sınırı aşıp aşmadığını anlamak için bir bayt fazla oku
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya çok büyük. En fazla {MAX_UPLOAD_MB} MB yükleyebilirsiniz."
        )

    filename = file.filename or ""
    is_pdf = filename.lower().endswith(".pdf")

    if is_pdf and not storage_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Dosya depolama servisi yapılandırılmamış; PDF şu an yüklenemiyor. Lütfen daha sonra tekrar deneyin."
        )

    file_type = "unknown"
    text_content = ""
    storage_key = None
    page_count = None
    processed_pages = None

    if is_pdf:
        file_type = "pdf"
        try:
            text_content, processed_pages, page_count = extract_text_from_pdf(content, max_pages=MAX_PDF_PAGES)
        except Exception:
            logger.exception("PDF okunamadı: %s", filename)
            raise HTTPException(status_code=400, detail="PDF dosyası okunamadı. Dosya bozuk veya şifreli olabilir.")

        storage_key = f"documents/{current_user['_id']}/{uuid.uuid4()}.pdf"
        try:
            storage_service.upload_file(storage_key, content, "application/pdf")
        except StorageError:
            raise HTTPException(status_code=503, detail="Dosya şu an kaydedilemedi, lütfen tekrar deneyin.")
    elif filename.lower().endswith(".txt"):
        file_type = "txt"
        text_content = content.decode("utf-8", errors="ignore")

    document_type = detect_document_type(text_content, filename)

    doc = document_record(
        user_id=current_user["_id"],
        original_name=filename,
        file_type=file_type,
        document_type=document_type,
        text_content=text_content,
        storage_key=storage_key,
        page_count=page_count,
        processed_pages=processed_pages
    )

    try:
        result = documents_collection.insert_one(doc)
    except Exception:
        # Kayıt oluşmadıysa depolamadaki dosya sahipsiz kalmasın
        if storage_key:
            try:
                storage_service.delete_file(storage_key)
            except StorageError:
                pass
        raise

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
        "originalName": filename,
        "fileType": file_type,
        "documentType": document_type,
        "pageCount": page_count,
        "processedPages": processed_pages,
        "truncated": truncated,
        "warning": warning
    }


@router.get("/{document_id}/file")
def get_document_file(document_id: str, current_user: dict = Depends(get_current_user)):
    try:
        doc = documents_collection.find_one({
            "_id": ObjectId(document_id),
            "userId": current_user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz document id.")

    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")

    storage_key = doc.get("storageKey")
    if storage_key:
        try:
            file_bytes = storage_service.download_file(storage_key)
        except StorageError:
            raise HTTPException(status_code=503, detail="Dosyaya şu an ulaşılamıyor, lütfen tekrar deneyin.")
        return Response(content=file_bytes, media_type="application/pdf")

    # Geriye dönük uyumluluk: eski belgelerde dosya base64 olarak Mongo'da duruyor
    file_data_b64 = doc.get("fileData", "")
    if file_data_b64:
        return Response(content=base64.b64decode(file_data_b64), media_type="application/pdf")

    raise HTTPException(status_code=404, detail="Bu belge için dosya verisi bulunamadı.")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        doc = documents_collection.find_one({
            "_id": ObjectId(document_id),
            "userId": current_user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz document id.")

    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")

    # Depolama hatası belge silmeyi engellemesin; storage_service hatayı zaten logluyor
    storage_key = doc.get("storageKey")
    if storage_key:
        try:
            storage_service.delete_file(storage_key)
        except StorageError:
            logger.warning("Belge silindi ama depolamadaki dosya silinemedi: %s", storage_key)

    documents_collection.delete_one({"_id": ObjectId(document_id)})
    analyses_collection.delete_many({"documentId": document_id})
    notes_collection.delete_many({"documentId": document_id, "userId": current_user["_id"]})

    return {"ok": True, "message": "Belge silindi."}
