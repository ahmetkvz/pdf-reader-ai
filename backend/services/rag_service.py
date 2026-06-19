import chromadb

client = chromadb.PersistentClient(path="./chroma_db")


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


def get_collection(document_id: str):
    collection_name = f"doc_{document_id}"
    return client.get_or_create_collection(name=collection_name)


def index_document(document_id: str, text: str):
    collection = get_collection(document_id)

    existing = collection.count()
    if existing > 0:
        collection.delete(ids=[str(i) for i in range(existing)])

    chunks = chunk_text(text)
    if not chunks:
        return 0

    collection.add(
        documents=chunks,
        ids=[str(i) for i in range(len(chunks))]
    )
    return len(chunks)


def query_document(document_id: str, question: str, top_k: int = 6) -> list:
    collection = get_collection(document_id)

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, collection.count())
    )

    return results["documents"][0] if results["documents"] else []
