import fitz
from PIL import Image
from transformers import DetrImageProcessor, DetrForObjectDetection, TableTransformerForObjectDetection
from torchvision import transforms
import torch
import easyocr
import numpy as np

from utility import MaxResize, get_cell_coordinates_by_row, objects_to_crops, outputs_to_objects

NOT_IDENTIFIED_VALUE = "N/A"


class TableExtractor:
    _detr_model = DetrForObjectDetection.from_pretrained(
        "Dilipan/detr-finetuned-invoice", id2label={0: "ItemTable"}, ignore_mismatched_sizes=True)
    _processor = DetrImageProcessor.from_pretrained(
        "Dilipan/detr-finetuned-invoice")
    _structure_model = TableTransformerForObjectDetection.from_pretrained(
        "microsoft/table-structure-recognition-v1.1-all")
    _reader = easyocr.Reader(['en'])

    _detection_class_thresholds = {
        "ItemTable": 0.8,
        "no object": 10
    }

    def __init__(self):
        self._device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        self._detr_model.to(self._device)
        self._structure_model.to(self._device)

        self.detection_transform = transforms.Compose([
            MaxResize(800),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        self.structure_transform = transforms.Compose([
            MaxResize(1000),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _apply_ocr(self, image, cell_coordinates):
        data = dict()
        max_num_columns = 0

        for idx, row in enumerate(cell_coordinates):
            row_text = []
            for cell in row["cells"]:
                cell_image = np.array(image.crop(cell["cell"]))
                result = self._reader.readtext(np.array(cell_image))

                if len(result) > 0:
                    text = " ".join([x[1] for x in result])
                    row_text.append(text)
                else:
                    row_text.append(NOT_IDENTIFIED_VALUE)

            if len(row_text) > max_num_columns:
                max_num_columns = len(row_text)

            data[idx] = row_text

            # pad rows which don't have max_num_columns elements
            # to make sure all rows have the same number of columns
            for row, row_data in data.copy().items():
                if len(row_data) != max_num_columns:
                    row_data = row_data + \
                        ["" for _ in range(max_num_columns - len(row_data))]
                    data[row] = row_data

        # Remove empty row and columns
        data = {key: row_data for key, row_data in data.items() if not all(
            val == NOT_IDENTIFIED_VALUE for val in row_data)}
        num_cols = len(next(iter(data.values())))
        data = {key: [row_data[i] for i in range(num_cols) if not all(
            data[j][i] == NOT_IDENTIFIED_VALUE for j in data)] for key, row_data in data.items()}

        return data

    def extract_item_table_from_image(self, img_path):
        result = []

        try:
            tokens = []
            image = Image.open(img_path)

            pixel_values = self.detection_transform(image).unsqueeze(0)
            pixel_values = pixel_values.to(self._device)

            # Item Table detection
            with torch.no_grad():
                outputs = self._detr_model(pixel_values)

            id2label = self._detr_model.config.id2label
            id2label[len(self._detr_model.config.id2label)] = "no object"

            objects = outputs_to_objects(outputs, image.size, id2label)

            # Crop Table
            tables_crops = objects_to_crops(
                image, tokens, objects, self._detection_class_thresholds, padding=5)
            cropped_table = tables_crops[0]['image'].convert("RGB")

            # Item table structure recognition
            pixel_values = self.structure_transform(cropped_table).unsqueeze(0)
            pixel_values = pixel_values.to(self._device)
            with torch.no_grad():
                outputs = self._structure_model(pixel_values)

            structure_id2label = self._structure_model.config.id2label
            structure_id2label[len(structure_id2label)] = "no object"

            cells = outputs_to_objects(
                outputs, cropped_table.size, structure_id2label)

            # Apply OCR
            cell_coordinates = get_cell_coordinates_by_row(cells)
            data = self._apply_ocr(cropped_table, cell_coordinates)

            for _, row_data in data.items():
                result.append(row_data)

        except Exception as e:
            print(f"Error processing {img_path}: {e}")

        return result

    # def extract_table_from_pdf(self, pdf_path):
    #     extracted_text = ""
    #     try:
    #         doc = fitz.open(pdf_path)
    #         for page in doc:
    #             extracted_text += page.get_text()
    #         doc.close()

    #         extracted_text = pytesseract.image_to_string(extracted_text)
    #     except Exception as e:
    #         print(f"Error processing {pdf_path}: {e}")

    #     return extracted_text
