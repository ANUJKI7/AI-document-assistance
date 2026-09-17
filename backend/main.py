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


# Enable CORS
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
# RAG
# =========================

print("Building RAG retriever...")

chunks, index = build_retriever()

print("RAG retriever is ready.")


# =========================
# Routes
# =========================

@app.get("/")
def home():

    return {
        "message": "AI Document Assistant is running!"
    }


@app.post("/upload")
def upload_document(
    file: UploadFile = File(...)
):

    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=file.filename
    )

    blob_client.upload_blob(
        file.file,
        overwrite=True
    )

    return {
        "message": "File uploaded successfully to Azure",
        "filename": file.filename
    }


@app.get("/ask")
def ask_question(question: str):

    # Retrieve relevant context
    context = retrieve_context(
        question,
        chunks,
        index,
        top_k=3
    )


    # Create prompt for Gemini
    prompt = f"""
You are an AI assistant that answers questions about a PDF document.

Use ONLY the information provided in the context below.

If the answer cannot be found in the context, say:

"I could not find the answer in the provided document."

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
        "answer": response.text
    }