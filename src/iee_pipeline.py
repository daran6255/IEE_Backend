import os
import cv2

from image_enhancer import ImageEnhancer
from text_extractor import TextExtractor
from entity_extractor import extractEntities
from text_preprocessor import TextPreprocessor
from table_extractor import TableExtractor

models_dir = r'models'


class IEEPipeline:
    image_enhancer = ImageEnhancer()
    text_extractor = TextExtractor()
    text_preprocessor = TextPreprocessor()
    entity_extractor = extractEntities(models_dir)
    table_extractor = TableExtractor()

    def __init__(self):
        pass

    def image_preprocessing(self, img_path):
        output_file = None
        image = cv2.imread(img_path)

        if image is not None:
            processed_image = self.image_enhancer.grayscale_conversion(image)

            base_name, extension = os.path.splitext(os.path.basename(img_path))
            output_file = os.path.join(os.path.dirname(
                img_path), f"{base_name}_ipp{extension}")

            cv2.imwrite(output_file, processed_image)

        return output_file

    def extract_text(self, img_path):
        response, output_text = self.text_extractor.extract_text_from_image(
            img_path)
        return response, output_text

    def text_preprocessing(self, text):
        cleaned_text = self.text_preprocessor.text_clean(text)
        tokens = self.text_preprocessor.text_tokenizer(cleaned_text)
        normalized_tokens = self.text_preprocessor.text_normalization(tokens)
        standardized_tokens = self.text_preprocessor.date_standardization(
            normalized_tokens)
        return ' '.join(standardized_tokens)

    def extract_entities(self, text):
        json_data = self.entity_extractor.extract_entities_spacy_tr(text)
        return json_data

    def extract_table_items(self, img_path, ocr_data):
        result = self.table_extractor.extract_item_table_from_image(
            img_path, ocr_data)
        return result
