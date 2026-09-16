import pypdfium2 as pdfium
import pytesseract


def extract_text_from_scanned_pdf(file_path):

    pdf = pdfium.PdfDocument(file_path)

    full_text = ""

    for page_number in range(len(pdf)):

        page = pdf[page_number]

        # Render PDF page as an image
        image = page.render(scale=2).to_pil()

        # OCR the image
        text = pytesseract.image_to_string(image)

        full_text += f"\n--- Page {page_number + 1} ---\n"
        full_text += text

        print(f"Processed page {page_number + 1}/{len(pdf)}")

    return full_text


if __name__ == "__main__":

    pdf_path = "uploads/(unit-5)the.pj.pdf"

    text = extract_text_from_scanned_pdf(pdf_path)

    print("\nCharacters extracted:", len(text))

    print("\nFirst 1000 characters:")
    print(text[:1000])