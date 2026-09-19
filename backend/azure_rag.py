import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery


load_dotenv()


SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")

INDEX_NAME = "documents-index"


if not SEARCH_ENDPOINT:
    raise ValueError("AZURE_SEARCH_ENDPOINT is missing from .env")

if not SEARCH_KEY:
    raise ValueError("AZURE_SEARCH_KEY is missing from .env")


print("Loading embedding model for Azure RAG...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY),
)


def retrieve_from_azure(question, top_k=3):

    print("\n===== AZURE AI SEARCH RETRIEVAL =====")
    print("Question:", question)

    # Create embedding for the user's question
    question_embedding = embedding_model.encode(
        [question]
    )[0]

    # Create vector search query
    vector_query = VectorizedQuery(
        vector=question_embedding.tolist(),
        k_nearest_neighbors=top_k,
        fields="embedding",
    )

    # Search Azure AI Search
    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=[
            "document_id",
            "filename",
            "page",
            "text",
            "sha256",
        ],
        top=top_k,
    )

    retrieved_chunks = []

    for number, result in enumerate(results, start=1):

        chunk = {
            "document_id": result["document_id"],
            "filename": result["filename"],
            "page": result["page"],
            "text": result["text"],
            "sha256": result.get("sha256", ""),
        }

        retrieved_chunks.append(chunk)

        print(f"\n--- Result {number} ---")
        print("Filename:", chunk["filename"])
        print("Page:", chunk["page"])

    print(
        "\nTotal chunks retrieved:",
        len(retrieved_chunks)
    )

    return retrieved_chunks


def build_context(retrieved_chunks):

    context_parts = []

    for chunk in retrieved_chunks:

        context_parts.append(
            f"Source: {chunk['filename']}, "
            f"Page {chunk['page']}\n"
            f"{chunk['text']}"
        )

    return "\n\n".join(context_parts)