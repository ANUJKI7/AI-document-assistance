import os

from dotenv import load_dotenv
from google import genai

from rag_retriever import build_retriever, retrieve_context


# Load environment variables
load_dotenv()

# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set in the .env file"
    )


# Create Gemini client
client = genai.Client(api_key=api_key)


# Build the RAG retriever
print("Building RAG retriever...")
chunks, index = build_retriever()


# Ask user for question
question = input(
    "\nAsk a question about the PDF: "
)


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


# Send context + question to Gemini
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt
)


print("\n===== GEMINI RAG ANSWER =====")
print(response.text)