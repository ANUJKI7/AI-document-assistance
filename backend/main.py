from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from backend.rag_retriever import build_retriever, retrieve_context
from backend.storage import save_rag_state, load_rag_state
from backend.azure_rag import retrieve_from_azure, build_context
from backend.azure_search_uploader import upload_chunks_to_azure

from google import genai

import os
import hashlib


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI()


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# AZURE STORAGE CONFIGURATION
# =========================================================

AZURE_CONNECTION_STRING = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

CONTAINER_NAME = os.getenv(
    "AZURE_STORAGE_CONTAINER"
)


blob_service_client = BlobServiceClient.from_connection_string(
    AZURE_CONNECTION_STRING
)


# =========================================================
# GEMINI CONFIGURATION
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set in the .env file"
    )


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# RAG STORAGE
# =========================================================

# All chunks from all unique documents
all_chunks = []


# One FAISS index shared by all documents
# We are keeping this for now as a fallback/local copy.
index = None


# Information about uploaded documents
documents = {}


# SHA-256 hash information
document_hashes = {}


# =========================================================
# LOAD PERSISTENT RAG DATA WHEN SERVER STARTS
# =========================================================

@app.on_event("startup")
def load_existing_rag_data():

    global index
    global all_chunks
    global documents
    global document_hashes

    (
        index,
        all_chunks,
        documents,
        document_hashes
    ) = load_rag_state()

    print("\n===== RAG STORAGE LOADED =====")

    print(
        "Documents:",
        len(documents)
    )

    print(
        "Chunks:",
        len(all_chunks)
    )

    if index is not None:

        print(
            "FAISS vectors:",
            index.ntotal
        )

    else:

        print(
            "FAISS vectors: 0"
        )

    print(
        "SHA-256 hashes:",
        len(document_hashes)
    )


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "AI Document Assistant is running!"
    }


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    global all_chunks
    global index
    global documents
    global document_hashes


    # -----------------------------------------------------
    # Check file type
    # -----------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        return {
            "error": "Only PDF files are supported."
        }


    # -----------------------------------------------------
    # Save PDF locally
    # -----------------------------------------------------

    os.makedirs(
        "uploads",
        exist_ok=True
    )


    file_path = os.path.join(
        "uploads",
        file.filename
    )


    with open(
        file_path,
        "wb"
    ) as buffer:

        while True:

            data = await file.read(
                1024 * 1024
            )

            if not data:
                break

            buffer.write(data)


    saved_size = os.path.getsize(
        file_path
    )


    print(
        "Original filename:",
        file.filename
    )

    print(
        "Saved file size:",
        saved_size,
        "bytes"
    )


    # =====================================================
    # CALCULATE SHA-256
    # =====================================================

    sha256_hash = hashlib.sha256()


    with open(
        file_path,
        "rb"
    ) as file_data:

        while True:

            data = file_data.read(
                1024 * 1024
            )

            if not data:
                break

            sha256_hash.update(data)


    file_hash = sha256_hash.hexdigest()


    print(
        "SHA-256:",
        file_hash
    )

    # =====================================================
    # UPLOAD TO AZURE BLOB STORAGE
    # =====================================================

    print("\n===== UPLOAD STARTED =====") 

    print(
        "Filename:",
        file.filename
    )

    blob_name = os.path.basename(file_path)

    print(
        "Blob name:",
        blob_name
    )

    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=blob_name
    )

    BLOCK_SIZE = 1024 * 1024  # 1 MB

    block_ids = []

    with open(file_path, "rb") as data:

        block_number = 0

        while True:

            block_data = data.read(BLOCK_SIZE)

            if not block_data:
                break

            block_id = f"{block_number:06d}"

            block_ids.append(block_id)

            print(
                f"Uploading block {block_number + 1} "
                f"({len(block_data)} bytes)..."
            )

            blob_client.stage_block(
                block_id=block_id,
                data=block_data,
                timeout=120
            )

            block_number += 1


    print("All blocks uploaded.")

    print("Committing blocks...")

    blob_client.commit_block_list(
        block_ids
    )

    print(
        "Uploaded to Azure Blob Storage."
    )
    # =====================================================
    # CHECK SHA-256 DUPLICATE
    # =====================================================

    if file_hash in document_hashes:

        existing_document = document_hashes[file_hash]


        existing_document_id = existing_document[
            "document_id"
        ]


        existing_filename = existing_document[
            "filename"
        ]


        # Find existing chunks using document ID
        existing_chunks = [

            chunk

            for chunk in all_chunks

            if chunk["document_id"] == existing_document_id
        ]


        print(
            "\n===== DUPLICATE DOCUMENT DETECTED ====="
        )

        print(
            "SHA-256 already exists."
        )

        print(
            "Existing document:",
            existing_filename
        )

        print(
            "Existing document ID:",
            existing_document_id
        )

        print(
            "Reusing existing chunks and embeddings."
        )

        print(
            "No new vectors added to FAISS."
        )


        # Store the new filename as another reference
        documents[file.filename] = {

            "document_id":
                existing_document_id,

            "chunks":
                len(existing_chunks),

            "sha256":
                file_hash,

            "original_filename":
                existing_filename
        }


        # Save updated document metadata
        save_rag_state(

            index,

            all_chunks,

            documents,

            document_hashes
        )


        return {

            "message":
                "This document already exists. "
                "Existing chunks and embeddings were reused.",

            "filename":
                file.filename,

            "document_id":
                existing_document_id,

            "chunks":
                len(existing_chunks),

            "total_documents":
                len(documents),

            "total_chunks":
                len(all_chunks),

            "total_vectors":
                index.ntotal,

            "sha256":
                file_hash,

            "reused":
                True
        }


    # =====================================================
    # NEW DOCUMENT
    # =====================================================

    print(
        "\nNew document detected."
    )

    print(
        "Building RAG index for uploaded document..."
    )


    new_chunks, index, embeddings = build_retriever(
    file_path,
    existing_index=index
    )


    # =====================================================
    # UPLOAD CHUNKS TO AZURE AI SEARCH
    # =====================================================

    azure_uploaded = upload_chunks_to_azure(
    new_chunks,
    embeddings,
    document_hash=file_hash
    )

    print(
     "Azure AI Search chunks uploaded:",
      azure_uploaded
    )


    # Add new chunks
    all_chunks.extend(
        new_chunks
    )


    # Get document ID
    document_id = new_chunks[0]["document_id"]


    # =====================================================
    # STORE DOCUMENT INFORMATION
    # =====================================================

    documents[file.filename] = {

        "document_id":
            document_id,

        "chunks":
            len(new_chunks),

        "sha256":
            file_hash,

        "original_filename":
            file.filename
    }


    # Store SHA-256 information
    document_hashes[file_hash] = {

        "document_id":
            document_id,

        "filename":
            file.filename,

        "chunks":
            new_chunks
    }


    # =====================================================
    # SAVE RAG STATE
    # =====================================================

    save_rag_state(

        index,

        all_chunks,

        documents,

        document_hashes
    )


    print(
        "RAG index updated successfully."
    )


    print(
        "Total documents:",
        len(documents)
    )


    print(
        "Total chunks:",
        len(all_chunks)
    )


    print(
        "Total vectors in FAISS:",
        index.ntotal
    )


    return {

        "message":
            "Document uploaded and processed successfully.",

        "filename":
            file.filename,

        "document_id":
            document_id,

        "chunks":
            len(new_chunks),

        "total_documents":
            len(documents),

        "total_chunks":
            len(all_chunks),

        "total_vectors":
            index.ntotal,

        "sha256":
            file_hash,

        "reused":
            False
    }


# =========================================================
# ASK QUESTION
# =========================================================

@app.get("/ask")
def ask_question(
    question: str
):

    global all_chunks
    global index


    # -----------------------------------------------------
    # Check whether documents exist
    # -----------------------------------------------------

    if not all_chunks:

        return {

            "error":
                "Please upload a PDF before asking a question."
        }


    # =====================================================
    # RETRIEVE RELEVANT CHUNKS FROM AZURE AI SEARCH
    # =====================================================

    retrieved_chunks = retrieve_from_azure(
        question,
        top_k=3
    )


    if not retrieved_chunks:

        return {
            "error":
                "No relevant information was found "
                "in Azure AI Search."
        }


    context = build_context(
        retrieved_chunks
    )


    # =====================================================
    # GEMINI PROMPT
    # =====================================================

    prompt = f"""
You are an AI assistant that answers questions
about uploaded PDF documents.

Use ONLY the information provided in the context below.

The context may contain information from multiple documents.

If the answer cannot be found in the context, say:

"I could not find the answer in the provided documents."

Do not use outside knowledge.

Context:
{context}

Question:
{question}

Answer clearly and concisely.
"""


    # =====================================================
    # GENERATE ANSWER
    # =====================================================

    response = gemini_client.models.generate_content(

        model="gemini-3.6-flash",

        contents=prompt
    )


    return {

        "answer":
            response.text
    }