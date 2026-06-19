from fastapi import APIRouter, HTTPException
from bson import ObjectId

from db.mongo import users_collection
from models.user_model import user_document
from schemas.auth_schema import RegisterRequest, LoginRequest
from core.security import hash_password, verify_password, create_access_token
from fastapi import APIRouter, HTTPException, Depends
from core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(data: RegisterRequest):
    existing_user = users_collection.find_one({"email": data.email.lower().strip()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı.")

    hashed = hash_password(data.password)
    user = user_document(
        name=data.name,
        email=data.email,
        password_hash=hashed
    )

    result = users_collection.insert_one(user)

    token = create_access_token({
        "sub": str(result.inserted_id),
        "email": data.email.lower().strip()
    })

    return {
        "ok": True,
        "message": "Kayıt başarılı.",
        "userId": str(result.inserted_id),
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/login")
def login(data: LoginRequest):
    user = users_collection.find_one({"email": data.email.lower().strip()})
    if not user:
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı.")

    if not verify_password(data.password, user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı.")

    token = create_access_token({
        "sub": str(user["_id"]),
        "email": user["email"]
    })

    return {
        "ok": True,
        "message": "Giriş başarılı.",
        "userId": str(user["_id"]),
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "ok": True,
        "user": {
            "id": current_user["_id"],
            "name": current_user["name"],
            "email": current_user["email"]
        }
    }

import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel
from services.email_service import send_reset_email


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    user = users_collection.find_one({"email": data.email.lower().strip()})
    if not user:
        return {"ok": True, "message": "Eğer bu email kayıtlıysa, sıfırlama bağlantısı gönderildi."}

    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"resetToken": reset_token, "resetTokenExpires": expires_at}}
    )

    reset_link = f"https://project-716py.vercel.app/reset-password?token={reset_token}"
    send_reset_email(data.email, reset_token, reset_link)

    return {"ok": True, "message": "Eğer bu email kayıtlıysa, sıfırlama bağlantısı gönderildi."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    user = users_collection.find_one({"resetToken": data.token})

    if not user:
        raise HTTPException(status_code=400, detail="Geçersiz veya kullanılmış bağlantı.")

    expires_at = user.get("resetTokenExpires")
    if not expires_at or datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Bağlantının süresi dolmuş.")

    new_hashed = hash_password(data.new_password)

    users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"passwordHash": new_hashed},
            "$unset": {"resetToken": "", "resetTokenExpires": ""}
        }
    )

    return {"ok": True, "message": "Şifre başarıyla sıfırlandı."}
