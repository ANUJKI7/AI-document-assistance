from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from backend.rag_retriever import build_retriever, retrieve_context

from google import genai

import os


# Load environment variables
load_dotenv()


# Create FastAPI application
app = FastAPI()


# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Azure Storage configuration
AZURE_CONNECTION_STRING = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

CONTAINER_NAME = os.getenv(
    "AZURE_STORAGE_CONTAINER"
)


blob_service_client = BlobServiceClient.from_connection_string(
    AZURE_CONNECTION_STRING
)


# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set in the .env file"
    )


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# MULTI-DOCUMENT RAG STORAGE
# =========================================================

# All chunks from all uploaded documents
all_chunks = []


# One FAISS index shared by all documents
index = None


# Information about uploaded documents
documents = {}


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


    # Check file type
    if not file.filename.lower().endswith(".pdf"):

        return {
            "error": "Only PDF files are supported."
        }


    # Prevent duplicate filename in current prototype
    if file.filename in documents:

        return {
            "message": "This document is already uploaded.",
            "filename": file.filename,
            "document_id": documents[file.filename]["document_id"],
            "chunks": documents[file.filename]["chunks"]
        }


    # Create uploads directory
    os.makedirs(
        "uploads",
        exist_ok=True
    )


    # Save uploaded PDF locally
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
    # UPLOAD TO AZURE BLOB STORAGE
    # =====================================================

    print("\n===== UPLOAD STARTED =====")

    print(
        "Filename:",
        file.filename
    )


    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=file.filename
    )


    with open(
        file_path,
        "rb"
    ) as data:

        blob_client.upload_blob(
            data,
            overwrite=True
        )


    print(
        "Uploaded to Azure Blob Storage."
    )


    # =====================================================
    # BUILD RAG FOR THIS DOCUMENT
    # =====================================================

    print(
        "\nBuilding RAG index for uploaded document..."
    )


    new_chunks, index = build_retriever(
        file_path,
        existing_index=index
    )


    # Add new document chunks to global chunk list
    all_chunks.extend(
        new_chunks
    )


    # Get document ID
    document_id = new_chunks[0]["document_id"]


    # Store document information
    documents[file.filename] = {

        "document_id": document_id,

        "chunks": len(new_chunks)
    }


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
            index.ntotal
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


    # Check whether any documents have been uploaded
    if index is None or not all_chunks:

        return {
            "error":
                "Please upload a PDF before asking a question."
        }


    # Retrieve relevant chunks from ALL documents
    context = retrieve_context(
        question,
        all_chunks,
        index,
        top_k=3
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


    # Generate answer
    response = gemini_client.models.generate_content(

        model="gemini-3.6-flash",

        contents=prompt
    )


    return {

        "answer":
            response.text
    }