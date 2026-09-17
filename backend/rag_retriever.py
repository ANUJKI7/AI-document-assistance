from pdf_processor import extract_pages_from_pdf
from chunker import create_chunks
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


# --------------------------------------------------
# STEP 1: Load embedding model
# --------------------------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# --------------------------------------------------
# STEP 2: PDF location
# --------------------------------------------------

pdf_path = "uploads/DC Machine1.pdf"


# --------------------------------------------------
# STEP 3: Extract text from PDF
# --------------------------------------------------

print("Reading PDF...")

pages = extract_pages_from_pdf(pdf_path)

total_characters = sum(
    len(page["text"])
    for page in pages
)

print("Characters extracted:", total_characters)


# --------------------------------------------------
# STEP 4: Create page-aware chunks
# --------------------------------------------------

chunks = create_chunks(pages)

print("Chunks created:", len(chunks))


# --------------------------------------------------
# STEP 5: Create embeddings
# --------------------------------------------------

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


# --------------------------------------------------
# STEP 6: Store embeddings in FAISS
# --------------------------------------------------

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

print("Vectors stored in FAISS:", index.ntotal)


# --------------------------------------------------
# STEP 7: Ask a question
# --------------------------------------------------

question = input("\nAsk a question about the PDF: ")


# --------------------------------------------------
# STEP 8: Convert question into embedding
# --------------------------------------------------

question_embedding = model.encode(
    [question]
)

question_embedding = np.array(
    question_embedding,
    dtype="float32"
)


# --------------------------------------------------
# STEP 9: Search FAISS
# --------------------------------------------------

number_of_results = min(3, len(chunks))

distances, indices = index.search(
    question_embedding,
    number_of_results
)


# --------------------------------------------------
# STEP 10: Build retrieved context
# --------------------------------------------------

retrieved_context = ""

print("\n===== RELEVANT CHUNKS =====")

for i, index_number in enumerate(indices[0]):

    page_number = chunks[index_number]["page"]
    chunk_text = chunks[index_number]["text"]

    print(f"\n--- Result {i + 1} ---")
    print("Chunk number:", index_number)
    print("Page:", page_number)
    print("Distance:", distances[0][i])

    print("\nText:")
    print(chunk_text)

    # Add chunk to context
    retrieved_context += (
        f"\n--- Source: Page {page_number} ---\n"
        f"{chunk_text}\n"
    )


# --------------------------------------------------
# STEP 11: Display final context
# --------------------------------------------------

print("\n\n===== RETRIEVED CONTEXT =====")
print(retrieved_context)