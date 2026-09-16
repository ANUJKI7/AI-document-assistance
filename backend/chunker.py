from pdf_processor import extract_text_from_scanned_pdf


def create_chunks(text, chunk_size=1000, overlap=200):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start = end - overlap

    return chunks


if __name__ == "__main__":

    pdf_path = "uploads/(unit-5)the.pj.pdf"

    # 1. Extract text using OCR
    text = extract_text_from_scanned_pdf(pdf_path)

    print("\nTotal characters:", len(text))

    # 2. Split text into chunks
    chunks = create_chunks(text)

    print("Total chunks:", len(chunks))

    # 3. Display first 3 chunks
    for i, chunk in enumerate(chunks[:3]):

        print(f"\n========== CHUNK {i + 1} ==========")
        print(chunk[:500])