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


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Azure Blob Storage
# =========================

AZURE_CONNECTION_STRING = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

CONTAINER_NAME = os.getenv(
    "AZURE_STORAGE_CONTAINER"
)

blob_service_client = BlobServiceClient.from_connection_string(
    AZURE_CONNECTION_STRING
)


# =========================
# Gemini
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set in the .env file"
    )

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================
# RAG STATE
# =========================

chunks = None
index = None
current_document = None


# =========================
# Routes
# =========================

@app.get("/")
def home():

    return {
        "message": "AI Document Assistant is running!"
    }


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    global chunks
    global index
    global current_document


    # Check file type
    if not file.filename.lower().endswith(".pdf"):
        return {
            "error": "Only PDF files are supported."
        }


    # Create local uploads directory
    os.makedirs("uploads", exist_ok=True)


    # Local path for temporary processing
    file_path = os.path.join(
        "uploads",
        file.filename
    )


    # Save uploaded file locally
    with open(file_path, "wb") as buffer:

        while True:

            data = await file.read(1024 * 1024)

            if not data:
                break

            buffer.write(data)
    saved_size = os.path.getsize(file_path)

    print("Original filename:", file.filename)
    print("Saved file size:", saved_size, "bytes")


    print("\n===== UPLOAD STARTED =====")
    print("Filename:", file.filename)


    # Upload PDF to Azure Blob Storage
    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=file.filename
    )

    with open(file_path, "rb") as data:

        blob_client.upload_blob(
            data,
            overwrite=True
        )


    print("Uploaded to Azure Blob Storage.")


    # Build RAG index from THIS uploaded PDF
    print("\nBuilding RAG index for uploaded document...")

    chunks, index = build_retriever(file_path)

    current_document = file.filename

    print("RAG index created successfully.")


    return {
        "message": "Document uploaded and processed successfully.",
        "filename": file.filename,
        "chunks": len(chunks)
    }


@app.get("/ask")
def ask_question(question: str):

    global chunks
    global index
    global current_document


    # Make sure a document has been uploaded
    if chunks is None or index is None:

        return {
            "error": "Please upload a PDF before asking a question."
        }


    # Retrieve relevant context
    context = retrieve_context(
        question,
        chunks,
        index,
        top_k=3
    )


    # Prompt Gemini
    prompt = f"""
You are an AI assistant that answers questions about a PDF document.

Use ONLY the information provided in the context below.

If the answer cannot be found in the context, say:

"I could not find the answer in the provided document."

Do not use outside knowledge.

Document:
{current_document}

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
        "document": current_document,
        "answer": response.text
    }