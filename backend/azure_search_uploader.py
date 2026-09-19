import os
import numpy as np

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")

INDEX_NAME = "documents-index"


if not SEARCH_ENDPOINT:
    raise ValueError(
        "AZURE_SEARCH_ENDPOINT is missing from .env"
    )

if not SEARCH_KEY:
    raise ValueError(
        "AZURE_SEARCH_KEY is missing from .env"
    )


search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY)
)


def upload_chunks_to_azure(
    chunks,
    embeddings,
    document_hash=""
):

    if not chunks:
        return 0

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks does not match number of embeddings."
        )

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    print("\n===== AZURE AI SEARCH INGESTION =====")
    print("Chunks received:", len(chunks))
    print("Embedding shape:", embeddings.shape)

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
            f"{start + 1}-"
            f"{start + len(batch)}..."
        )

        try:

            results = search_client.upload_documents(
                documents=batch
            )

            successful = 0

            for result in results:

                if result.succeeded:
                    successful += 1
                else:
                    print(
                        "Upload failed:",
                        result.key,
                        result.error_message
                    )

            total_uploaded += successful

        except Exception as e:

            print(
                "Azure AI Search upload error:",
                e
            )

    print(
        "Total chunks uploaded:",
        total_uploaded
    )

    print(
        "Total chunks failed:",
        len(documents) - total_uploaded
    )

    return total_uploaded