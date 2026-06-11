from datetime import datetime

def analysis_record(
    user_id: str,
    document_id: str,
    summary: str = "",
    important_points: list | None = None,
    sensitive_findings: list | None = None,
    keywords: list | None = None
):
    return {
        "userId": user_id,
        "documentId": document_id,
        "summary": summary,
        "importantPoints": important_points or [],
        "sensitiveFindings": sensitive_findings or [],
        "keywords": keywords or [],
        "createdAt": datetime.utcnow()
    }