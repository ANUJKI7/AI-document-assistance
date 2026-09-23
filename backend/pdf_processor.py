from pypdf import PdfReader
import pypdfium2 as pdfium
import numpy as np
from paddleocr import PaddleOCR


# Load PaddleOCR once
_ocr = None


def get_ocr():
    global _ocr

    if _ocr is None:
        print("Loading PaddleOCR...")
        _ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
    )
    return _ocr


def extract_pages_from_pdf(file_path):
    reader = PdfReader(file_path)
    pdf = pdfium.PdfDocument(file_path)

    pages = []

    pypdf_pages = 0
    ocr_pages = 0

    print("Total pages:", len(reader.pages))

    for page_number in range(len(reader.pages)):

        # -------------------------------------------------
        # STEP 1: Try normal PDF text extraction
        # -------------------------------------------------
        page_text = reader.pages[page_number].extract_text()

        if page_text and page_text.strip():

            text = page_text

            pypdf_pages += 1

            print(
                f"Page {page_number + 1}: pypdf"
            )

        # -------------------------------------------------
        # STEP 2: If no text, use PaddleOCR
        # -------------------------------------------------
        else:

            page = pdf[page_number]

            image = page.render(scale=3).to_pil()

            # PaddleOCR requires NumPy array or file path
            image = np.array(image)

            ocr = get_ocr()

            result = ocr.predict(image)

            texts = []

            if result:
                texts = result[0]["rec_texts"]

            text = "\n".join(texts)

            ocr_pages += 1

            print(
                f"Page {page_number + 1}: PaddleOCR"
            )

        pages.append(
            {
                "page": page_number + 1,
                "text": text,
            }
        )

    # -------------------------------------------------
    # EXTRACTION SUMMARY
    # -------------------------------------------------

    print("\n===== EXTRACTION SUMMARY =====")

    print(
        "Pages extracted with pypdf:",
        pypdf_pages
    )

    print(
        "Pages processed with PaddleOCR:",
        ocr_pages
    )

    return pages


if __name__ == "__main__":

    pdf_path = "uploads/unit 5.pdf"

    pages = extract_pages_from_pdf(pdf_path)

    total_characters = sum(
        len(page["text"])
        for page in pages
    )

    print(
        "Total characters extracted:",
        total_characters
    )

    print("\n===== FIRST PAGE =====")

    print(
        pages[0]["text"][:2000]
    )