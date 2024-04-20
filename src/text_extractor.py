import os
import fitz
import pytesseract
from PIL import Image

if os.getenv('PLATFORM') == 'win':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class TextExtractor:

    def __init__(self):
        self.pdf_files = []

    def extract_text_from_image(self, img_path):
        extracted_text = ""

        try:
            custom_config = r'--oem 3 --psm 6'
            extracted_text = pytesseract.image_to_string(
                Image.open(img_path), config=custom_config)
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

        return extracted_text

    def extract_text_from_pdf(self, pdf_path):
        extracted_text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                extracted_text += page.get_text()
            doc.close()

            extracted_text = pytesseract.image_to_string(extracted_text)
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

        return extracted_text
