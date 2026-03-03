"""
services/memory_service.py — Long Term Memory via ChromaDB.
Handles storing PDF contents, PRDs, and important conversation context.
"""
import os
from core.logging_config import get_logger
from core.config import settings

# Force using pysqlite3 for ChromaDB if sqlite3 is outdated (common on Linux)
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = get_logger(__name__)

# Initialize ChromaDB client (local persistent storage)
os.makedirs(settings.CHROMA_PATH, exist_ok=True)
_chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)

# Use sentence-transformers embedding model
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=settings.EMBEDDING_MODEL
)

# Get or create the main collection
# Using cosine similarity for better semantic distance metrics
_collection = _chroma_client.get_or_create_collection(
    name="ba_agent_memory",
    embedding_function=_embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

# We use standard langchain chunker
_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " ", ""]
)


def add_to_memory(text: str, source_name: str, additional_metadata: dict = None) -> int:
    """
    Chunks text and stores it in the vector DB for future retrieval.
    """
    if not text or not text.strip():
        return 0

    chunks = _text_splitter.split_text(text)
    if not chunks:
        return 0

    documents = []
    metadatas = []
    ids = []

    base_meta = {"source": source_name}
    if additional_metadata:
        base_meta.update(additional_metadata)

    import uuid
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append(base_meta)
        ids.append(f"{source_name}_{uuid.uuid4().hex[:8]}_{i}")

    try:
        _collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(chunks)} chunks to memory from '{source_name}'.")
        return len(chunks)
    except Exception as e:
        logger.error(f"Failed to add to memory: {e}")
        return 0


def search_memory(query: str, k: int = 3) -> str:
    """
    Searches the vector DB for the most relevant context chunks.
    Returns them as a single concatenated string.
    """
    if not query or not query.strip():
        return ""
        
    try:
        if _collection.count() == 0:
            return ""

        results = _collection.query(
            query_texts=[query],
            n_results=k
        )
        
        retrieved_texts = results.get("documents", [[]])[0]
        retrieved_metadatas = results.get("metadatas", [[]])[0]

        if not retrieved_texts:
            return ""

        context_blocks = []
        for i, txt in enumerate(retrieved_texts):
            source = retrieved_metadatas[i].get("source", "Unknown") if i < len(retrieved_metadatas) else "Unknown"
            context_blocks.append(f"[Source: {source}]\n{txt.strip()}")

        final_context = "\n\n".join(context_blocks)
        logger.info(f"Retrieved {len(retrieved_texts)} chunks from memory for query.")
        return final_context

    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        return ""
