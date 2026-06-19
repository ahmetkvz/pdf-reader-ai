from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime

from db.mongo import documents_collection, analyses_collection
from core.dependencies import get_current_user
from services.analysis_service import _ask_groq
from services.rag_service import query_document

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("/{document_id}")
def chat_with_document(
    document_id: str,
    body: ChatRequest,
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

    relevant_chunks = query_document(document_id, body.question, top_k=6)

    if relevant_chunks:
        context = "\n\n---\n\n".join(relevant_chunks)
    else:
        context = doc.get("textContent", "").strip()[:4000]

    if not context:
        raise HTTPException(status_code=400, detail="Belge içeriği boş.")

    prompt = f"""Sen bir belge asistanısın. Sana belge içinden alınmış parçalar verilecek.
KURALLAR:
1. SADECE aşağıda verilen belge parçalarındaki bilgiyi kullan.
2. Kendi genel bilgini, dışarıdan bilgiyi veya tahminini KESİNLİKLE kullanma.
3. Eğer cevap parçalarda yoksa, sadece şunu yaz: "Bu bilgi belgede yer almıyor."
4. Cevabı SADECE Türkçe yaz, başka dilden kelime kullanma.
5. Cevap belgede varsa, belgedeki ifadelere sadık kalarak özetle.

Belge parçaları:
{context}

Soru: {body.question}

Cevap:"""

    answer = _ask_groq(prompt)

    message = {
        "question": body.question,
        "answer": answer,
        "timestamp": datetime.utcnow().isoformat()
    }

    analyses_collection.update_one(
        {
            "documentId": document_id,
            "userId": current_user["_id"]
        },
        {"$push": {"chatHistory": message}},
        upsert=True
    )

    return {
        "ok": True,
        "question": body.question,
        "answer": answer,
        "timestamp": message["timestamp"]
    }


@router.get("/{document_id}")
def get_chat_history(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    analysis = analyses_collection.find_one({
        "documentId": document_id,
        "userId": current_user["_id"]
    })

    if not analysis:
        return {"ok": True, "chatHistory": []}

    return {
        "ok": True,
        "chatHistory": analysis.get("chatHistory", [])
    }
