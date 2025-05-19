from pdf2image import convert_from_path
import pytesseract
import os

def extract_text_from_pdf(pdf_path):
    print(f"📄 Reading PDF: {pdf_path}")
    images = convert_from_path(pdf_path)
    full_text = ""

    for i, image in enumerate(images):
        print(f"🔍 OCR on page {i+1}...")
        text = pytesseract.image_to_string(image)
        full_text += f"\n--- Page {i+1} ---\n{text}"

    return full_text

def save_to_file(text, output_path):
    with open(output_path, "w") as f:
        f.write(text)
    print(f"✅ Text saved to {output_path}")

if __name__ == "__main__":
    input_file = "data/antonios_cv.pdf"
    output_text_file = "data/parsed_text.txt"

    if not os.path.exists(input_file):
        print("❌ PDF file not found. Please add it to the /data folder.")
    else:
        text = extract_text_from_pdf(input_file)
        save_to_file(text, output_text_file)