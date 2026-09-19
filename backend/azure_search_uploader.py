import json
import os

import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = "documents-index"

CHUNKS_FILE = "data/chunks.json"


if not SEARCH_ENDPOINT:
    raise ValueError("AZURE_SEARCH_ENDPOINT is missing from .env")

if not SEARCH_KEY:
    raise ValueError("AZURE_SEARCH_KEY is missing from .env")


print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")


search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY),
)


def upload_chunks():

    if not os.path.exists(CHUNKS_FILE):
        raise FileNotFoundError(
            f"Could not find {CHUNKS_FILE}. "
            "Make sure your local RAG data exists."
        )

    print("Loading chunks...")

    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    print("Total chunks:", len(chunks))

    if not chunks:
        raise ValueError("No chunks found in chunks.json.")

    print()
    print("Creating embeddings...")

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    print("Embedding shape:", embeddings.shape)

    documents = []

    for i, chunk in enumerate(chunks):

        document = {
            "id": f"{chunk['document_id']}_{i}",
            "document_id": chunk["document_id"],
            "filename": chunk["filename"],
            "page": chunk["page"],
            "text": chunk["text"],
            "embedding": embeddings[i].tolist(),
            "sha256": "",
        }

        documents.append(document)

    print()
    print("Uploading documents to Azure AI Search...")

    batch_size = 100

    total_uploaded = 0

    for start in range(0, len(documents), batch_size):

        batch = documents[start:start + batch_size]

        results = search_client.upload_documents(
            documents=batch
        )

        successful = sum(
            1 for result in results
            if result.succeeded
        )

        failed = len(results) - successful

        total_uploaded += successful

        print(
            f"Batch {start // batch_size + 1}: "
            f"{successful} uploaded, "
            f"{failed} failed"
        )

        if failed > 0:
            for result in results:
                if not result.succeeded:
                    print(
                        "Upload error:",
                        result.error_message
                    )

    print()
    print("========================================")
    print("Azure upload completed")
    print("========================================")
    print("Total chunks:", len(chunks))
    print("Successfully uploaded:", total_uploaded)
    print("Index:", INDEX_NAME)
    print()


if __name__ == "__main__":
    upload_chunks()