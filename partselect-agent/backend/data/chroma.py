from pathlib import Path
from typing import Optional

import chromadb

BASE_DIR = Path(__file__).parent
CHROMA_PATH = BASE_DIR / "chroma"
COLLECTION_NAME = "repair_articles"


def get_client(persist_path: str | Path = CHROMA_PATH) -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(persist_path))


def get_collection(
    client: Optional[chromadb.ClientAPI] = None,
    embedding_function=None,
) -> chromadb.Collection:
    if client is None:
        client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )
