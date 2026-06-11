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
)

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def analyze_cv(text: str):
    summary = simple_summary(text, max_sentences=5, max_chars=900)
    keywords = extract_keywords(text, top_n=12)
    important_points = extract_important_points(text, limit=6)
    sensitive_findings = detect_sensitive(text)

    cv_sections = {
        "profileSummary": summary,
        "strongSides": [],
        "technicalSkills": [],
        "experienceHighlights": [],
        "improvementSuggestions": []
    }

    lower = text.lower()

    if "backend" in lower or "api" in lower:
        cv_sections["strongSides"].append("Backend development ve API entegrasyonu alanında deneyim/ilgi görülüyor.")

    if "mongodb" in lower or "sql" in lower or "mssql" in lower:
        cv_sections["strongSides"].append("Veritabanı teknolojileriyle çalışma deneyimi bulunuyor.")

    if "llm" in lower or "rag" in lower or "artificial intelligence" in lower:
        cv_sections["strongSides"].append("Yapay zekâ, LLM ve RAG tabanlı projelere yönelik deneyim bulunuyor.")

    if "intern" in lower or "staj" in lower:
        cv_sections["experienceHighlights"].append("Staj deneyimleri CV içinde açık şekilde belirtilmiş.")

    skill_candidates = [
        "python", "java", "javascript", "c#", "c++", "c",
        "react", "node.js", "mongodb", "mssql", "fastapi",
        ".net", "asp.net", "rest api", "postman", "git", "github",
        "llm", "rag", "swagger"
    ]

    for skill in skill_candidates:
        if skill in lower:
            cv_sections["technicalSkills"].append(skill)

    cv_sections["technicalSkills"] = sorted(set(cv_sections["technicalSkills"]))

    if "github" not in lower:
        cv_sections["improvementSuggestions"].append("CV’ye GitHub profil linki eklenebilir.")

    if "project" not in lower and "projects" not in lower:
        cv_sections["improvementSuggestions"].append("Projeler bölümü daha görünür hale getirilebilir.")

    if "english" not in lower and "ingilizce" not in lower:
        cv_sections["improvementSuggestions"].append("Dil seviyesi bilgisi eklenebilir.")

    if not cv_sections["improvementSuggestions"]:
        cv_sections["improvementSuggestions"].append("CV genel olarak yeterli görünüyor; proje açıklamaları daha ölçülebilir sonuçlarla güçlendirilebilir.")

    return {
        "summary": summary,
        "importantPoints": important_points,
        "sensitiveFindings": sensitive_findings,
        "keywords": keywords,
        "documentSpecificAnalysis": cv_sections
    }


def analyze_lecture_note(text: str):
    summary = simple_summary(text, max_sentences=6, max_chars=1000)
    keywords = extract_keywords(text, top_n=15)
    important_points = extract_important_points(text, limit=8)
    sensitive_findings = detect_sensitive(text)

    exam_notes = []

    for point in important_points:
        exam_notes.append(f"Sınav için dikkat: {point}")

    lecture_sections = {
        "lessonSummary": summary,
        "keyConcepts": keywords,
        "examFocusedNotes": exam_notes[:5],
        "studySuggestions": [
            "Önce ana kavramları kısa tanımlarıyla tekrar et.",
            "Daha sonra örnek soru-cevap mantığıyla konuyu pekiştir.",
            "Sayısal veya formüllü kısımlar varsa ayrıca küçük bir formül listesi çıkar.",
            "Sınav öncesi önemli noktaları madde madde tekrar et."
        ]
    }

    return {
        "summary": summary,
        "importantPoints": important_points,
        "sensitiveFindings": sensitive_findings,
        "keywords": keywords,
        "documentSpecificAnalysis": lecture_sections
    }


def analyze_general_document(text: str):
    summary = simple_summary(text, max_sentences=5, max_chars=900)
    keywords = extract_keywords(text, top_n=10)
    important_points = extract_important_points(text, limit=5)
    sensitive_findings = detect_sensitive(text)

    general_sections = {
        "generalSummary": summary,
        "mainTopics": keywords,
        "documentWarnings": []
    }

    if sensitive_findings:
        general_sections["documentWarnings"].append(
            "Bu belgede hassas veri olabilecek bilgiler tespit edildi."
        )
    else:
        general_sections["documentWarnings"].append(
            "Belgede belirgin bir hassas veri tespit edilmedi."
        )

    return {
        "summary": summary,
        "importantPoints": important_points,
        "sensitiveFindings": sensitive_findings,
        "keywords": keywords,
        "documentSpecificAnalysis": general_sections
    }


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

    if document_type == "cv":
        analysis_result = analyze_cv(text)

    elif document_type == "lecture_note":
        analysis_result = analyze_lecture_note(text)

    else:
        analysis_result = analyze_general_document(text)

    summary = analysis_result["summary"]
    important_points = analysis_result["importantPoints"]
    sensitive_findings = analysis_result["sensitiveFindings"]
    keywords = analysis_result["keywords"]
    document_specific_analysis = analysis_result["documentSpecificAnalysis"]

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
                "summary": analysis_data["summary"],
                "importantPoints": analysis_data["importantPoints"],
                "sensitiveFindings": analysis_data["sensitiveFindings"],
                "keywords": analysis_data["keywords"],
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