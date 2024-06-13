from PIL import Image
from transformers import DetrImageProcessor, DetrForObjectDetection, TableTransformerForObjectDetection
from torchvision import transforms
import torch

# from PIL import Image, ImageDraw

from src.data_processor import DataProcessor
from src.utility import MaxResize, get_cell_coordinates_by_row, objects_to_crops, outputs_to_objects, convert_to_pixels

NOT_IDENTIFIED_VALUE = "N/A"

column_keywords = {
    "ITEMNAME": ["Item Desc", "Item", "Description", "Product", "Product Name", "Description of Goods"],
    "HSN": ["HSN Code", "HSN", "Item Code", "Product Code"],
    "QUANTITY": ["Qty", "Quantity", "Qty."],
    "UNIT": ["Unit", "Units"],
    "PRICE": ["Cost", "Price", "Rate", "Unit Price", "Price/Unit"],
    "AMOUNT": ["Amt", "Amount", "Total", "Total Amount", "Total Cost"]
}


class TableExtractor:
    _detection_class_thresholds = {
        "ItemTable": 0.8,
        "no object": 10
    }
    _detection_transform = transforms.Compose([
        MaxResize(800),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    _structure_transform = transforms.Compose([
        MaxResize(1000),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    def __init__(self):
        self._data_processor = DataProcessor(keywords=column_keywords)
        self._detr_model = DetrForObjectDetection.from_pretrained(
            "Dilipan/detr-finetuned-invoice", id2label={0: "ItemTable"}, ignore_mismatched_sizes=True)
        self._processor = DetrImageProcessor.from_pretrained(
            "Dilipan/detr-finetuned-invoice")
        self._structure_model = TableTransformerForObjectDetection.from_pretrained(
            "microsoft/table-structure-recognition-v1.1-all")

        self._device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")

        self._detr_model.to(self._device)
        self._structure_model.to(self._device)

    def _is_text_in_cell(self, text, cell):
        # Calculate the area of the intersection
        x_overlap = max(0, min(text['Right'], cell['Right']
                               ) - max(text['Left'], cell['Left']))
        y_overlap = max(
            0, min(text['Bottom'], cell['Bottom']) - max(text['Top'], cell['Top']))
        intersection_area = x_overlap * y_overlap

        text_area = (text['Right'] - text['Left']) * \
            (text['Bottom'] - text['Top'])

        # Check if more than half of the text is in the cell
        return intersection_area >= 0.5 * text_area

    def _map_table_cell_and_text(self, image, cell_data, ocr_data):
        data = dict()
        max_num_columns = 0
        img_w, img_h = image.size

        # draw = ImageDraw.Draw(image)

        for idx, row in enumerate(cell_data):
            row_text = []
            for cell in row["cells"]:
                result = ''
                for block in ocr_data['Blocks']:
                    if block['BlockType'] == 'WORD':
                        text_coords = {
                            'Left': block['Geometry']['BoundingBox']['Left'],
                            'Top': block['Geometry']['BoundingBox']['Top'],
                            'Width': block['Geometry']['BoundingBox']['Width'],
                            'Height': block['Geometry']['BoundingBox']['Height']
                        }

                        text_coords = convert_to_pixels(
                            text_coords, img_w, img_h)

                        cell_coords = {
                            'Left': cell['cell'][0],
                            'Top': cell['cell'][1],
                            'Right': cell['cell'][2],
                            'Bottom': cell['cell'][3]
                        }

                        # draw.rectangle([(text_coords['Left'], text_coords['Top']),
                        #                 (text_coords['Right'], text_coords['Bottom'])], outline="red")

                        # draw.rectangle([(cell_coords['Left'], cell_coords['Top']),
                        #                 (cell_coords['Right'], cell_coords['Bottom'])], outline="red")

                        if self._is_text_in_cell(text_coords, cell_coords):
                            result = result + ' ' + block['Text']

                        # Optimization - Break if table cell coordinate maxes text coordinates
                        # break

                if result == '':
                    row_text.append(NOT_IDENTIFIED_VALUE)
                else:
                    row_text.append(result)

            if len(row_text) > max_num_columns:
                max_num_columns = len(row_text)

            data[idx] = row_text

            # pad rows which don't have max_num_columns elements
            # to make sure all rows have the same number of columns
            for row, row_data in data.copy().items():
                if len(row_data) != max_num_columns:
                    row_data = row_data + \
                        ["" for _ in range(
                            max_num_columns - len(row_data))]
                    data[row] = row_data

        # Remove empty row and columns
        data = {key: row_data for key, row_data in data.items() if not all(
            val == NOT_IDENTIFIED_VALUE for val in row_data)}
        num_cols = len(next(iter(data.values())))
        data = {key: [row_data[i] for i in range(num_cols) if not all(
            data[j][i] == NOT_IDENTIFIED_VALUE for j in data)] for key, row_data in data.items()}

        # image.save('temp/table_bb.jpg')

        return data

    def extract_item_table_from_image(self, img_path, ocr_data):
        result = []

        try:
            tokens = []
            image = Image.open(img_path)

            pixel_values = self._detection_transform(image).unsqueeze(0)
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
            pixel_values = self._structure_transform(
                cropped_table).unsqueeze(0)
            pixel_values = pixel_values.to(self._device)
            with torch.no_grad():
                outputs = self._structure_model(pixel_values)

            structure_id2label = self._structure_model.config.id2label
            structure_id2label[len(structure_id2label)] = "no object"

            cells = outputs_to_objects(
                outputs, cropped_table.size, structure_id2label, tables_crops[0]['origin'])

            # Apply OCR
            cell_coordinates = get_cell_coordinates_by_row(cells)
            data = self._map_table_cell_and_text(
                image, cell_coordinates, ocr_data)

            for _, row_data in data.items():
                result.append(row_data)

        except Exception as e:
            print(f"Error processing {img_path}: {e}")

        return result

    def map_table_columns(self, table, ner_output=None):
        if table:
            new_header = self._data_processor.process_table_data(
                table=table, ner_output=ner_output)
            return new_header
        else:
            print(f"Error: Table data not provided")

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
