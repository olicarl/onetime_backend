import pypdf
import sys

def extract_text(pdf_path, output_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        with open(output_path, "w", encoding="utf-8") as f:
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                f.write(f"--- Page {i+1} ---\n")
                f.write(text)
                f.write("\n")
        print(f"Successfully extracted text to {output_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_text("FHWA-2022-0008-0403_attachment_6.pdf", "pdf_content.txt")
