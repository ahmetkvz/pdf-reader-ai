from pydantic import BaseModel


class DocumentResponse(BaseModel):
    ok: bool
    message: str
    documentId: str
    originalName: str
    storedFilename: str
    fileType: str
    documentType: str