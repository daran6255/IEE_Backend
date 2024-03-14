import cv2
import os
import numpy as np
from skimage.transform import rotate
from skimage.color import rgb2gray
from deskew import determine_skew
import imutils

# Define the input and output folders
input_folder = r'C:\Users\WVF-DL-90\Desktop\Invoice_Entities_Extraction\data\dataset\img_correction'
output_folder = r'C:\Users\WVF-DL-90\Desktop\Invoice_Entities_Extraction\data\dataset\img_correction_final'



# Process images in the input folder
for filename in os.listdir(input_folder):
    # Read the image
    image_path = os.path.join(input_folder, filename)
    image = cv2.imread(image_path)
    processed_image =image



    # Apply image processing steps
    # processed_image= cv2.fastNlMeansDenoisingColored(processed_image,None,10,10,7,21) 
    # processed_image = cv2.cvtColor(image
    #                           , cv2.COLOR_BGR2GRAY)
    # angle = determine_skew(processed_image)                    
    # rotated = rotate(processed_image, angle, resize=True) * 255
    # processed_image=rotated.astype(np.uint8)
    # processed_image = cv2.adaptiveThreshold(processed_image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
    #         cv2.THRESH_BINARY,11,2) 
    
    # norm_img = np.zeros((processed_image.shape[0], processed_image.shape[1]))
    # processed_image = cv2.normalize(processed_image, norm_img, 0, 255, cv2.NORM_MINMAX)
    # processed_image=cv2.fastNlMeansDenoisingColored(processed_image, None, 10, 10, 7, 15)
    # kernel = np.ones((2,3),np.uint8)
    # processed_image = cv2.erode(processed_image, kernel, iterations = 1)
    # processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
    # processed_image = cv2.threshold(processed_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) [1]
    
    processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
    processed_image = cv2.threshold(processed_image, 0, 255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    dist = cv2.distanceTransform(processed_image, cv2.DIST_L2, 5)
    dist = cv2.normalize(dist, dist, 0, 1.0, cv2.NORM_MINMAX)
    dist = (dist * 255).astype("uint8")
    processed_image = cv2.threshold(dist, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    # processed_image = cv2.morphologyEx(processed_image, cv2.MORPH_OPEN, kernel)
    
    # cnts = cv2.findContours(processed_image.copy(), cv2.RETR_EXTERNAL,
	# cv2.CHAIN_APPROX_SIMPLE)
    # cnts = imutils.grab_contours(cnts)
    # chars = []
    # # loop over the contours
    # for c in cnts:
    #     # compute the bounding box of the contour
    #     (x, y, w, h) = cv2.boundingRect(c)
    #     # check if contour is at least 35px wide and 100px tall, and if
    #     # so, consider the contour a digit
    #     if w >= 35 and h >= 100:
    #         chars.append(c)
    # print(chars)
    # chars = np.vstack([chars[i] for i in range(0, len(chars))])
    # hull = cv2.convexHull(chars)
    # # allocate memory for the convex hull mask, draw the convex hull on
    # # the image, and then enlarge it via a dilation
    # mask = np.zeros(image.shape[:2], dtype="uint8")
    # cv2.drawContours(mask, [hull], -1, 255, -1)
    # mask = cv2.dilate(mask, None, iterations=2)
    # processed_image = cv2.bitwise_and(processed_image, processed_image, mask=mask)
    kernel = np.ones((1, 1), np.uint8)
    processed_image = cv2.dilate(processed_image, kernel, iterations=1)

    # Save the processed image to the output folder
    output_path = os.path.join(output_folder, filename)
    cv2.imwrite(output_path, processed_image)

    print(f'Processed {filename} and saved output to {output_path}')
