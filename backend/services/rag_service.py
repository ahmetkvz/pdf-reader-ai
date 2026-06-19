import re
from collections import Counter

_STORE = {}


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 40) -> list:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def _tokenize(text: str) -> list:
    text = text.lower()
    text = re.sub(r"[^\wçğıöşüâî\s]", " ", text)
    return [w for w in text.split() if len(w) > 2]


def index_document(document_id: str, text: str):
    chunks = chunk_text(text)
    if not chunks:
        return 0

    indexed = []
    for chunk in chunks:
        tokens = _tokenize(chunk)
        indexed.append({"text": chunk, "tokens": Counter(tokens)})

    _STORE[document_id] = indexed
    return len(chunks)


def query_document(document_id: str, question: str, top_k: int = 9) -> list:
    if document_id not in _STORE:
        return []

    indexed = _STORE[document_id]
    q_tokens = set(_tokenize(question))

    if not q_tokens:
        return [c["text"] for c in indexed[:top_k]]

    scored = []
    for chunk in indexed:
        score = sum(chunk["tokens"][t] for t in q_tokens if t in chunk["tokens"])
        overlap_count = sum(1 for t in q_tokens if t in chunk["tokens"])
        scored.append((score + overlap_count, chunk["text"]))

    scored.sort(key=lambda x: -x[0])
    top = [text for score, text in scored[:top_k] if score > 0]

    if not top:
        top = [c["text"] for c in indexed[:top_k]]

    return top
