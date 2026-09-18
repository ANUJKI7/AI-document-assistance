from backend.pdf_processor import extract_pages_from_pdf
from backend.chunker import create_chunks

from sentence_transformers import SentenceTransformer

import faiss
import numpy as np


# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


def build_retriever(pdf_path):

    print("Reading PDF...")

    # Extract text
    pages = extract_pages_from_pdf(pdf_path)

    total_characters = sum(
        len(page["text"])
        for page in pages
    )

    print("Characters extracted:", total_characters)

    # Create chunks
    chunks = create_chunks(pages)

    print("Chunks created:", len(chunks))

    # Create embeddings
    print("\nCreating embeddings...")

    chunk_texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        chunk_texts,
        show_progress_bar=True
    )

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    print("Embedding shape:", embeddings.shape)

    # Create FAISS index
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    print("Vectors stored in FAISS:", index.ntotal)

    return chunks, index


def retrieve_context(question, chunks, index, top_k=3):

    # Create embedding for question
    question_embedding = model.encode(
        [question]
    )

    question_embedding = np.array(
        question_embedding,
        dtype="float32"
    )

    # Search FAISS
    number_of_results = min(
        top_k,
        len(chunks)
    )

    distances, indices = index.search(
        question_embedding,
        number_of_results
    )

    retrieved_context = ""

    print("\n===== RETRIEVED CHUNKS =====")

    for i, index_number in enumerate(indices[0]):

        page_number = chunks[index_number]["page"]
        chunk_text = chunks[index_number]["text"]

        print(f"\n--- Result {i + 1} ---")
        print("Page:", page_number)
        print("Distance:", distances[0][i])
        print("Text:")
        print(chunk_text)

        retrieved_context += (
            f"\n--- Source: Page {page_number} ---\n"
            f"{chunk_text}\n"
        )

    return retrieved_context