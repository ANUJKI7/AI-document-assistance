from pypdf import PdfReader
import pypdfium2 as pdfium
import pytesseract


def extract_pages_from_pdf(file_path):
    reader = PdfReader(file_path)
    pdf = pdfium.PdfDocument(file_path)

    pages = []

    pypdf_pages = 0
    ocr_pages = 0

    print("Total pages:", len(reader.pages))

    for page_number in range(len(reader.pages)):

        # Try normal text extraction first
        page_text = reader.pages[page_number].extract_text()

        if page_text and page_text.strip():
            text = page_text
            pypdf_pages += 1
            print(f"Page {page_number + 1}: pypdf")

        else:
            # If there is no usable text, use OCR
            page = pdf[page_number]
            image = page.render(scale=2).to_pil()

            text = pytesseract.image_to_string(image)

            ocr_pages += 1
            print(f"Page {page_number + 1}: OCR")

        pages.append({
            "page": page_number + 1,
            "text": text
        })

    print("\n===== EXTRACTION SUMMARY =====")
    print("Pages extracted with pypdf:", pypdf_pages)
    print("Pages processed with OCR:", ocr_pages)

    return pages


if __name__ == "__main__":

    pdf_path = "uploads/DC Machine1.pdf"

    pages = extract_pages_from_pdf(pdf_path)

    total_characters = sum(len(page["text"]) for page in pages)

    print("Total characters extracted:", total_characters)

    print("\n===== FIRST PAGE =====")
    print(pages[0]["text"][:2000])