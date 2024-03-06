import os
import cv2

from image_enhancer import ImageEnhancer


class IEEPipeline:
    imageEnhancer = ImageEnhancer()
    
    def __init__(self):
        pass
    
    def image_preprocessing(self, img_path):
        output_file = None
        image = cv2.imread(img_path)
        
        if image is not None:
            processed_image = self.imageEnhancer.grayscale_conversion(image)

            base_name, extension = os.path.splitext(os.path.basename(img_path))
            output_file = os.path.join(os.path.dirname(img_path), f"{base_name}_ipp{extension}")

            cv2.imwrite(output_file, processed_image)
            
        return output_file

    
    def extract_text(self, img_path):
        extracted_text = "kjhfakhfkaf kjahfkasjf"
        return extracted_text
    
    def text_preprocessing(self, text):
        
        pass
    
    def extract_entities(self, text):
        
        return {"invioce_no": 1233}