from datetime import datetime

def chat_record(
    user_id: str,
    document_id: str,
    question: str,
    answer: str
):
    return {
        "userId": user_id,
        "documentId": document_id,
        "question": question,
        "answer": answer,
        "createdAt": datetime.utcnow()
    }