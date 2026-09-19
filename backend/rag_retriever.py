import os
import uuid

from backend.pdf_processor import extract_pages_from_pdf
from backend.chunker import create_chunks

from backend.embedding_model import get_embedding_model

import faiss
import numpy as np




def build_retriever(pdf_path, existing_index=None):

    print("Reading PDF...")

    # Create document information
    filename = os.path.basename(pdf_path)
    document_id = str(uuid.uuid4())

    print("Document ID:", document_id)
    print("Filename:", filename)

    # Extract text from PDF
    pages = extract_pages_from_pdf(pdf_path)

    total_characters = sum(
        len(page["text"])
        for page in pages
    )

    print("Characters extracted:", total_characters)

    # Create chunks with metadata
    chunks = create_chunks(
        pages,
        document_id,
        filename
    )

    print("Chunks created:", len(chunks))

    if not chunks:
        raise ValueError("No text could be extracted from the PDF.")

    # Create embeddings
    print("\nCreating embeddings...")

    chunk_texts = [
        chunk["text"]
        for chunk in chunks
    ]

    model = get_embedding_model()
    embeddings = model.encode(
        chunk_texts,
        show_progress_bar=True
    )

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    print("Embedding shape:", embeddings.shape)

    # Create a new FAISS index only if one does not already exist
    if existing_index is None:

        dimension = embeddings.shape[1]

        index = faiss.IndexFlatL2(dimension)

        print("Created new FAISS index.")

    else:

        index = existing_index

        # Make sure the embedding dimensions match
        if index.d != embeddings.shape[1]:
            raise ValueError(
                "Embedding dimension does not match existing FAISS index."
            )

        print("Using existing FAISS index.")

    # Add new document embeddings to the index
    index.add(embeddings)

    print("Vectors stored in FAISS:", index.ntotal)

    return chunks, index, embeddings


def retrieve_context(question, chunks, index, top_k=3):

    question_embedding = model.encode(
        [question]
    )

    question_embedding = np.array(
        question_embedding,
        dtype="float32"
    )

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

        document_id = chunks[index_number]["document_id"]
        filename = chunks[index_number]["filename"]
        page_number = chunks[index_number]["page"]
        chunk_text = chunks[index_number]["text"]

        print(f"\n--- Result {i + 1} ---")
        print("Document ID:", document_id)
        print("Filename:", filename)
        print("Page:", page_number)
        print("Distance:", distances[0][i])
        print("Text:")
        print(chunk_text)

        retrieved_context += (
            f"\n--- Source: {filename}, Page {page_number} ---\n"
            f"{chunk_text}\n"
        )

    return retrieved_context