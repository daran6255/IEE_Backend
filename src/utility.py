import os
import torch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class MaxResize(object):
    def __init__(self, max_size=800):
        self.max_size = max_size

    def __call__(self, image):
        width, height = image.size
        current_max_size = max(width, height)
        scale = self.max_size / current_max_size
        resized_image = image.resize(
            (int(round(scale*width)), int(round(scale*height))))

        return resized_image


def box_cxcywh_to_xyxy(x):
    x_c, y_c, w, h = x.unbind(-1)
    b = [(x_c - 0.5 * w), (y_c - 0.5 * h), (x_c + 0.5 * w), (y_c + 0.5 * h)]
    return torch.stack(b, dim=1)


def rescale_bboxes(out_bbox, size):
    img_w, img_h = size
    b = box_cxcywh_to_xyxy(out_bbox)
    b = b * torch.tensor([img_w, img_h, img_w, img_h], dtype=torch.float32)
    return b


def outputs_to_objects(outputs, img_size, id2label, crop_origin=None):
    m = outputs.logits.softmax(-1).max(-1)
    pred_labels = list(m.indices.detach().cpu().numpy())[0]
    pred_scores = list(m.values.detach().cpu().numpy())[0]
    pred_bboxes = outputs['pred_boxes'].detach().cpu()[0]
    pred_bboxes = [elem.tolist()
                   for elem in rescale_bboxes(pred_bboxes, img_size)]

    objects = []
    for label, score, bbox in zip(pred_labels, pred_scores, pred_bboxes):
        class_label = id2label[int(label)]
        if not class_label == 'no object':
            if crop_origin is not None:
                # Convert the coordinates to be relative to the original image
                bbox = [bbox[0] + crop_origin[0], bbox[1] + crop_origin[1],
                        bbox[2] + crop_origin[0], bbox[3] + crop_origin[1]]
            objects.append({'label': class_label, 'score': float(score),
                            'bbox': [float(elem) for elem in bbox]})

    return objects


def objects_to_crops(img, tokens, objects, class_thresholds, padding=10):
    """
    Process the bounding boxes produced by the table detection model into
    cropped table images and cropped tokens.
    """

    table_crops = []
    for obj in objects:
        if obj['score'] < class_thresholds[obj['label']]:
            continue

        cropped_table = {}

        bbox = obj['bbox']
        bbox = [bbox[0]-padding, bbox[1]-padding,
                bbox[2]+padding, bbox[3]+padding]

        cropped_img = img.crop(bbox)

        table_tokens = [token for token in tokens if iob(
            token['bbox'], bbox) >= 0.5]
        for token in table_tokens:
            token['bbox'] = [token['bbox'][0]-bbox[0],
                             token['bbox'][1]-bbox[1],
                             token['bbox'][2]-bbox[0],
                             token['bbox'][3]-bbox[1]]

        cropped_table['image'] = cropped_img
        cropped_table['tokens'] = table_tokens
        cropped_table['origin'] = (bbox[0], bbox[1])

        table_crops.append(cropped_table)

    return table_crops


def get_cell_coordinates_by_row(table_data):
    rows = [entry for entry in table_data if entry['label'] == 'table row']
    columns = [entry for entry in table_data if entry['label'] == 'table column']

    # Sort rows and columns by their Y and X coordinates, respectively
    rows.sort(key=lambda x: x['bbox'][1])
    columns.sort(key=lambda x: x['bbox'][0])

    def find_cell_coordinates(row, column):
        cell_bbox = [column['bbox'][0], row['bbox']
                     [1], column['bbox'][2], row['bbox'][3]]
        return cell_bbox

    # Generate cell coordinates and count cells in each row
    cell_coordinates = []

    for row in rows:
        row_cells = []
        for column in columns:
            cell_bbox = find_cell_coordinates(row, column)
            row_cells.append({'column': column['bbox'], 'cell': cell_bbox})

        # Sort cells in the row by X coordinate
        row_cells.sort(key=lambda x: x['column'][0])

        # Append row information to cell_coordinates
        cell_coordinates.append(
            {'row': row['bbox'], 'cells': row_cells, 'cell_count': len(row_cells)})

    # Sort rows from top to bottom
    cell_coordinates.sort(key=lambda x: x['row'][1])

    return cell_coordinates


def send_email(user_email, token):
    host_url = os.getenv('HOST')
    email_domain = os.getenv('EMAIL_DOMAIN')
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')

    smtplibObj = smtplib.SMTP(email_domain, 587)
    smtplibObj.starttls()
    smtplibObj.login(email_address, email_password)

    msg = MIMEMultipart()
    msg['From'] = email_address
    msg['To'] = user_email
    msg['Subject'] = "IEE Email Confirmation"
    body = f"Please confirm your email by clicking on the following link: {host_url}/verify-email/{token}"
    msg.attach(MIMEText(body, 'plain'))

    smtplibObj.send_message(msg)
    del msg

    smtplibObj.quit()


def convert_to_pixels(box, image_width, image_height):
    left = box['Left'] * image_width
    top = box['Top'] * image_height
    right = (box['Left'] + box['Width']) * image_width
    bottom = (box['Top'] + box['Height']) * image_height
    return {'Left': left, 'Top': top, 'Right': right, 'Bottom': bottom}
