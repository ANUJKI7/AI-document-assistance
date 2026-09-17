from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


# -----------------------------
# 1. Load embedding model
# -----------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# -----------------------------
# 2. Chunking function
# -----------------------------

def create_chunks(text, chunk_size=1000, overlap=200):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start = end - overlap

    return chunks


# -----------------------------
# 3. Load PDF and create chunks
# -----------------------------

pdf_path = "uploads/DC Machine1.pdf"

print("Reading PDF and extracting text...")

reader = PdfReader(pdf_path)

text = ""

for page in reader.pages:
    page_text = page.extract_text()

    if page_text:
        text += page_text + "\n"

print("Characters extracted:", len(text))


chunks = create_chunks(text)

print("Chunks created:", len(chunks))


# -----------------------------
# 4. Create embeddings
# -----------------------------

print("\nCreating embeddings...")

embeddings = model.encode(
    chunks,
    show_progress_bar=True
)

embeddings = np.array(
    embeddings,
    dtype="float32"
)

print("Embedding shape:", embeddings.shape)


# -----------------------------
# 5. Create FAISS index
# -----------------------------

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

print("Vectors stored in FAISS:", index.ntotal)


# -----------------------------
# 6. Ask a question
# -----------------------------

question = input("\nAsk a question about the PDF: ")

question_embedding = model.encode(
    [question]
)

question_embedding = np.array(
    question_embedding,
    dtype="float32"
)


# -----------------------------
# 7. Search FAISS
# -----------------------------

number_of_results = 3

distances, indices = index.search(
    question_embedding,
    number_of_results
)


# -----------------------------
# 8. Display retrieved chunks
# -----------------------------

print("\n===== RELEVANT CHUNKS =====")

for i, index_number in enumerate(indices[0]):

    print(f"\n--- Result {i + 1} ---")

    print("Chunk number:", index_number)

    print("Distance:", distances[0][i])

    print("\nText:")

    print(chunks[index_number])