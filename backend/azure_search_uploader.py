import os

import numpy as np
from dotenv import load_dotenv
from backend.embedding_model import get_embedding_model

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = "documents-index"


if not SEARCH_ENDPOINT:
    raise ValueError("AZURE_SEARCH_ENDPOINT is missing from .env")

if not SEARCH_KEY:
    raise ValueError("AZURE_SEARCH_KEY is missing from .env")


# Load the SAME embedding model used by the existing RAG system.


search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY),
)


def upload_chunks_to_azure(chunks, document_hash=""):
    """
    Upload chunks and their embeddings to Azure AI Search.

    The chunks must already contain:
        document_id
        filename
        page
        text

    Returns the number of successfully uploaded chunks.
    """

    if not chunks:
        print("No chunks to upload to Azure AI Search.")
        return 0

    print("\n===== AZURE AI SEARCH INGESTION =====")
    print("Chunks to upload:", len(chunks))

    # --------------------------------------------------
    # Create embeddings
    # --------------------------------------------------

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print("Creating Azure Search embeddings...")

    embedding_model = get_embedding_model()
    embeddings = embedding_model.encode(texts, show_progress_bar=True)

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    print(
        "Embedding shape:",
        embeddings.shape
    )

    # --------------------------------------------------
    # Build Azure Search documents
    # --------------------------------------------------

    documents = []

    for position, chunk in enumerate(chunks):

        document = {
            "id": f"{chunk['document_id']}_{position}",
            "document_id": chunk["document_id"],
            "filename": chunk["filename"],
            "page": chunk["page"],
            "text": chunk["text"],
            "embedding": embeddings[position].tolist(),
            "sha256": document_hash,
        }

        documents.append(document)

    # --------------------------------------------------
    # Upload in batches
    # --------------------------------------------------

    batch_size = 100
    total_uploaded = 0

    for start in range(
        0,
        len(documents),
        batch_size
    ):

        batch = documents[
            start:start + batch_size
        ]

        print(
            f"Uploading batch "
            f"{start // batch_size + 1}..."
        )

        results = search_client.upload_documents(
            documents=batch
        )

        successful = sum(
            1
            for result in results
            if result.succeeded
        )

        failed = len(results) - successful

        total_uploaded += successful

        print(
            f"Uploaded: {successful}, "
            f"Failed: {failed}"
        )

        if failed > 0:

            for result in results:

                if not result.succeeded:

                    print(
                        "Azure Search upload error:",
                        result.error_message
                    )

    print(
        "Total successfully uploaded to Azure AI Search:",
        total_uploaded
    )

    return total_uploaded