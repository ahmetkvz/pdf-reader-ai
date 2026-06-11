from datetime import datetime

def user_document(name: str, email: str, password_hash: str):
    return {
        "name": name,
        "email": email.lower().strip(),
        "passwordHash": password_hash,
        "createdAt": datetime.utcnow()
    }