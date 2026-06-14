from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from db.mongo import documents_collection, analyses_collection
from core.dependencies import get_current_user
from models.analysis_model import analysis_record
from services.analysis_service import (
    simple_summary,
    detect_sensitive,
    extract_keywords,
    extract_important_points,
    analyze_cv_with_gemini,
    analyze_lecture_with_gemini,
    analyze_general_with_gemini,
    detect_document_type,
)

router = APIRouter(prefix="/analysis", tags=["Analysis"])


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

    summary = simple_summary(text)
    important_points = extract_important_points(text)
    sensitive_findings = detect_sensitive(text)
    keywords = extract_keywords(text)

    if document_type == "cv":
        document_specific_analysis = analyze_cv_with_gemini(text)
    elif document_type == "lecture_note":
        document_specific_analysis = analyze_lecture_with_gemini(text)
    else:
        document_specific_analysis = analyze_general_with_gemini(text)

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
