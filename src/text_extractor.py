import os
import io
import fitz
import boto3
import pytesseract
from PIL import Image

isProd = os.getenv('ENV') == 'prod'

if os.getenv('PLATFORM') == 'win':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class TextExtractor:
    _aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    _aws_secret_access_key = os.getenv('AWS_ACCESS_KEY')
    _region_name = os.getenv('AWS_REGION')

    def __init__(self):
        self.pdf_files = []

    def _use_tesseract(self, img_path):
        custom_config = r'--oem 3 --psm 6'
        return pytesseract.image_to_string(
            Image.open(img_path), config=custom_config)

    def _use_textract(self, img_path):
        text = ''
        textract = boto3.client(
            'textract',
            aws_access_key_id=self._aws_access_key_id,
            aws_secret_access_key=self._aws_secret_access_key,
            region_name=self._region_name
        )

        with io.open(img_path, 'rb') as image_file:
            image_bytes = image_file.read()

        response = textract.detect_document_text(
            Document={'Bytes': image_bytes}
        )

        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                text += item.get('Text', '') + ' '

        return text

    def extract_text_from_image(self, img_path):
        extracted_text = ""

        try:
            if isProd:
                extracted_text = self._use_textract(img_path)
            else:
                extracted_text = self._use_tesseract(img_path)

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

            # extracted_text = pytesseract.image_to_string(extracted_text)
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

        return extracted_text
