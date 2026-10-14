from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId
import logging

from db.mongo import documents_collection, analyses_collection
from core.dependencies import get_current_user
from models.analysis_model import analysis_record
from services.analysis_service import (
    analyze_document,
    detect_sensitive,
    AIServiceError,
    ai_call_scope,
)
from services.export_service import generate_analysis_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

AI_UNAVAILABLE_MESSAGE = "Yapay zeka servisine şu an ulaşılamıyor, lütfen tekrar deneyin."


@router.post("/run/{document_id}")
def run_analysis(document_id: str, current_user: dict = Depends(get_current_user)):
    try:
        doc = documents_collection.find_one({
            "_id": ObjectId(document_id),
            "userId": current_user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz document id.")

    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")

    text = doc.get("textContent", "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="Belge içinde analiz edilecek metin yok.")

    document_type = doc.get("documentType", "general")

    # Tüm yapay zeka çağrıları veritabanına yazmadan önce yapılır;
    # biri (uzun belgede herhangi bir parça dahil) başarısız olursa hiçbir sonuç kaydedilmez.
    success = False
    with ai_call_scope() as scope:
        try:
            result = analyze_document(text, document_type)
            summary = result["summary"]
            important_points = result["important_points"]
            keywords = result["keywords"]
            document_specific_analysis = result["document_specific"]
            success = True
        except AIServiceError:
            raise HTTPException(status_code=503, detail=AI_UNAVAILABLE_MESSAGE)
        finally:
            # Maliyet takibi için: kaç yapay zeka çağrısı yapıldı
            logger.info(
                "Analiz %s: belge=%s, %d karakter, %d yapay zeka çağrısı",
                "tamamlandı" if success else "başarısız", document_id, len(text), scope["calls"]
            )

    sensitive_findings = detect_sensitive(text)

    existing = analyses_collection.find_one({
        "documentId": document_id,
        "userId": current_user["_id"]
    })

    analysis_data = analysis_record(
        user_id=current_user["_id"],
        document_id=document_id,
        summary=summary,
        important_points=important_points,
        sensitive_findings=sensitive_findings,
        keywords=keywords
    )

    analysis_data["documentType"] = document_type
    analysis_data["documentSpecificAnalysis"] = document_specific_analysis

    if existing:
        analyses_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "summary": summary,
                "importantPoints": important_points,
                "sensitiveFindings": sensitive_findings,
                "keywords": keywords,
                "documentType": document_type,
                "documentSpecificAnalysis": document_specific_analysis
            }}
        )
        analysis_id = str(existing["_id"])
    else:
        result = analyses_collection.insert_one(analysis_data)
        analysis_id = str(result.inserted_id)

    return {
        "ok": True,
        "message": "Analiz tamamlandı.",
        "analysisId": analysis_id,
        "documentId": document_id,
        "documentType": document_type,
        "summary": summary,
        "importantPoints": important_points,
        "sensitiveFindings": sensitive_findings,
        "keywords": keywords,
        "documentSpecificAnalysis": document_specific_analysis
    }


@router.get("/{document_id}/export")
def export_analysis_pdf(document_id: str, current_user: dict = Depends(get_current_user)):
    analysis = analyses_collection.find_one({
        "documentId": document_id,
        "userId": current_user["_id"]
    })

    if not analysis:
        raise HTTPException(status_code=404, detail="Bu belge için analiz bulunamadı.")

    doc = documents_collection.find_one({"_id": ObjectId(document_id)})
    document_name = doc.get("originalName", "Belge") if doc else "Belge"

    pdf_buffer = generate_analysis_pdf(document_name, analysis)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=analiz_raporu.pdf"}
    )


@router.get("/{document_id}")
def get_analysis(document_id: str, current_user: dict = Depends(get_current_user)):
    analysis = analyses_collection.find_one({
        "documentId": document_id,
        "userId": current_user["_id"]
    })

    if not analysis:
        raise HTTPException(status_code=404, detail="Bu belge için analiz bulunamadı.")

    analysis["_id"] = str(analysis["_id"])

    return {
        "ok": True,
        "analysis": analysis
    }
