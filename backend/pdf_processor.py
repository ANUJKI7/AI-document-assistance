from pypdf import PdfReader
import pypdfium2 as pdfium
import pytesseract


def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    pdf = pdfium.PdfDocument(file_path)

    full_text = ""

    pypdf_pages = 0
    ocr_pages = 0

    print("Total pages:", len(reader.pages))

    for page_number in range(len(reader.pages)):

        # First try normal text extraction
        page_text = reader.pages[page_number].extract_text()

        if page_text and page_text.strip():
            full_text += f"\n--- Page {page_number + 1} ---\n"
            full_text += page_text

            pypdf_pages += 1
            print(f"Page {page_number + 1}: pypdf")

        else:
            # If no text exists, use OCR
            page = pdf[page_number]
            image = page.render(scale=2).to_pil()

            ocr_text = pytesseract.image_to_string(image)

            full_text += f"\n--- Page {page_number + 1} ---\n"
            full_text += ocr_text

            ocr_pages += 1
            print(f"Page {page_number + 1}: OCR")

    print("\n===== EXTRACTION SUMMARY =====")
    print("Pages extracted with pypdf:", pypdf_pages)
    print("Pages processed with OCR:", ocr_pages)
    print("Total characters extracted:", len(full_text))

    return full_text


if __name__ == "__main__":

    pdf_path = "uploads/DC Machine1.pdf"

    text = extract_text_from_pdf(pdf_path)

    print("\n===== FIRST 2000 CHARACTERS =====")
    print(text[:2000])