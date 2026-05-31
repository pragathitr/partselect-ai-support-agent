import os
from typing import Optional
import chromadb


def search_repair_articles(
    query: str,
    appliance_type: Optional[str] = None,
    n_results: int = 3,
    collection: Optional[chromadb.Collection] = None,
) -> list[dict]:
    """Semantic search over repair articles using Chroma.

    Pass `collection` in tests to avoid OpenAI calls.
    In production, pass None to use the persisted OpenAI-embedded collection.
    """
    where = {"appliance_type": appliance_type} if appliance_type else None

    if collection is None:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
        from backend.data.chroma import get_client, COLLECTION_NAME

        api_key = os.getenv("OPENAI_API_KEY")
        ef = OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-3-small")
        client = get_client()

        # Open without attaching an EF — avoids the persisted-vs-new EF conflict
        # check in newer Chroma versions. We embed the query manually and pass
        # query_embeddings so Chroma never needs to call an EF on the collection.
        try:
            collection = client.get_collection(name=COLLECTION_NAME, embedding_function=None)
        except Exception:
            return []  # collection not built yet — run: python -m backend.scripts.build_chroma

        count = collection.count()
        if count == 0:
            return []
        n_results = min(n_results, count)

        results = collection.query(
            query_embeddings=ef([query]),
            n_results=n_results,
            where=where,
        )
    else:
        # Test path: caller injects a collection that already has a mock EF.
        count = collection.count()
        if count == 0:
            return []
        n_results = min(n_results, count)

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )

    docs = results["documents"][0]
    ids = results["ids"][0]
    metas = results["metadatas"][0]
    distances = (results.get("distances") or [[None] * len(docs)])[0]

    return [
        {"id": ids[i], "content": doc, "metadata": metas[i], "distance": distances[i]}
        for i, doc in enumerate(docs)
    ]
