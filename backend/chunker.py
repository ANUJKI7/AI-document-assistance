def create_chunks(pages, document_id, filename, chunk_size=1000, overlap=200):
    chunks = []

    for page in pages:
        page_number = page["page"]
        text = page["text"]

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append({
                    "document_id": document_id,
                    "filename": filename,
                    "page": page_number,
                    "text": chunk_text
                })

            start = end - overlap

    return chunks