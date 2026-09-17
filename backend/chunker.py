def create_chunks(pages, chunk_size=1000, overlap=200):
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
                    "page": page_number,
                    "text": chunk_text
                })

            start = end - overlap

    return chunks


if __name__ == "__main__":

    sample_pages = [
        {
            "page": 1,
            "text": "A" * 2500
        },
        {
            "page": 2,
            "text": "B" * 1500
        }
    ]

    chunks = create_chunks(sample_pages)

    print("Number of chunks:", len(chunks))

    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1}")
        print("Page:", chunk["page"])
        print("Characters:", len(chunk["text"]))