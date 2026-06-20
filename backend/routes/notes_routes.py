from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from bson import ObjectId

from db.mongo import db
from core.dependencies import get_current_user

router = APIRouter(prefix="/notes", tags=["Notes"])
notes_collection = db["notes"]


class NoteRequest(BaseModel):
    content: str
    page_number: Optional[int] = None


@router.post("/{document_id}")
def create_note(
    document_id: str,
    body: NoteRequest,
    current_user: dict = Depends(get_current_user)
):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Not içeriği boş olamaz.")

    note = {
        "documentId": document_id,
        "userId": current_user["_id"],
        "content": body.content.strip(),
        "pageNumber": body.page_number,
        "createdAt": datetime.utcnow()
    }

    result = notes_collection.insert_one(note)

    return {
        "ok": True,
        "noteId": str(result.inserted_id),
        "content": note["content"],
        "pageNumber": note["pageNumber"],
        "createdAt": note["createdAt"].isoformat()
    }


@router.get("/{document_id}")
def get_notes(document_id: str, current_user: dict = Depends(get_current_user)):
    notes = list(notes_collection.find({
        "documentId": document_id,
        "userId": current_user["_id"]
    }).sort("createdAt", -1))

    for note in notes:
        note["_id"] = str(note["_id"])
        note["createdAt"] = note["createdAt"].isoformat()

    return {"ok": True, "notes": notes}


@router.delete("/{note_id}")
def delete_note(note_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = notes_collection.delete_one({
            "_id": ObjectId(note_id),
            "userId": current_user["_id"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz not id.")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not bulunamadı.")

    return {"ok": True, "message": "Not silindi."}
