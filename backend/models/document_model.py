from datetime import datetime


def document_record(
    user_id: str,
    original_name: str,
    stored_filename: str,
    file_type: str,
    document_type: str = "general",
    text_content: str = "",
    file_data: str = ""
):
    return {
        "userId": user_id,
        "originalName": original_name,
        "storedFilename": stored_filename,
        "fileType": file_type,
        "documentType": document_type,
        "textContent": text_content,
        "fileData": file_data,
        "uploadDate": datetime.utcnow()
    }
