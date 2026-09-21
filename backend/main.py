from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_routes import router as auth_router
from routes.document_routes import router as document_router
from routes.analysis_routes import router as analysis_router
from routes.chat_routes import router as chat_router
from routes.notes_routes import router as notes_router

app = FastAPI(title="PDF Reader AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://project-716py.vercel.app", "http://localhost:5173", "https://localhost", "capacitor://localhost", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'lar
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(analysis_router)
app.include_router(chat_router)
app.include_router(notes_router)


# -------------------------
# Default endpoints
# -------------------------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/ping")
def ping():
    return {"message": "pong"}
