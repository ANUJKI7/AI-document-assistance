from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER")

blob_service_client = BlobServiceClient.from_connection_string(
    AZURE_CONNECTION_STRING
)


@app.get("/")
def home():
    return {"message": "AI Document Assistant is running!"}


@app.get("/ask")
def ask_question(question: str):
    return {
        "answer": f"You asked: {question}"
    }


@app.post("/upload")
def upload_document(file: UploadFile = File(...)):

    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=file.filename
    )

    blob_client.upload_blob(file.file, overwrite=True)

    return {
        "message": "File uploaded successfully to Azure",
        "filename": file.filename
    }