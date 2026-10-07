from datetime import datetime


def document_record(
    user_id: str,
    original_name: str,
    file_type: str,
    document_type: str = "general",
    text_content: str = "",
    storage_key: str = None,
    page_count: int = None,
    processed_pages: int = None,
    stored_filename: str = None,
    file_data: str = ""
):
    record = {
        "userId": user_id,
        "originalName": original_name,
        "fileType": file_type,
        "documentType": document_type,
        "textContent": text_content,
        "storageKey": storage_key,
        "pageCount": page_count,
        "processedPages": processed_pages,
        "uploadDate": datetime.utcnow()
    }

    # Eski biçim: dosya diske ve base64 olarak Mongo'ya yazılıyordu.
    # Yeni yüklemeler bunları kullanmaz; dosya nesne depolamada durur (storageKey).
    if stored_filename:
        record["storedFilename"] = stored_filename
    if file_data:
        record["fileData"] = file_data

    return record
