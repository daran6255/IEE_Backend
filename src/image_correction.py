import cv2
import os
import numpy as np

# Define the input and output folders
input_folder = r'C:\Users\WVF-DL-90\Desktop\Invoice_Entities_Extraction\data\dataset\img_correction'
output_folder = r'C:\Users\WVF-DL-90\Desktop\Invoice_Entities_Extraction\data\dataset\img_correction_final'

# Function to apply grayscale conversion to an image
def grayscale_conversion(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray_image

# Function to apply noise reduction or removal (blur)
def noise_reduction(image):
    blurred_image = cv2.bilateralFilter(image, 15, 65, 65)
    return blurred_image

# Function to enhance image contrast
def enhance_contrast(image):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    equalized_image = clahe.apply(image)
    return equalized_image

# Function to apply adaptive thresholding
def global_thresholding(image):
    _, thresholded_image = cv2.threshold(image, 140, 255, cv2.THRESH_BINARY )
    return thresholded_image

# Function to apply adaptive thresholding
def adaptive_thresholding(image):
    thresholded_image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 5)
    return thresholded_image

# Function for background subtraction
# def background_subtraction(image):

#     background_subtractor = cv2.createBackgroundSubtractorMOG2()
#     background_subtracted_image = background_subtractor.apply(image)

#     return background_subtracted_image

# Function to enhance text edges
def enhance_text_edges(image):
    
    # Perform morphological opening to enhance text edges
    kernel = np.ones((3,3), np.uint8)
    opened = cv2.morphologyEx(image, cv2.MORPH_DILATE, kernel)
    edges = cv2.absdiff(opened, image)
    # Perform Canny edge detection
    # edges = cv2.Canny(opened, 50, 150)
    
    # Invert the edges to obtain the text edges
    
    # blurred_image = cv2.GaussianBlur(image, (3, 3), 0)
    # edges = cv2.Canny(blurred_image, 100, 200)
    inverted_edges = 255 - edges
    return inverted_edges

# Function to perform morphological operations
def morphological_operations(image):

    # Perform morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    morphed_image = cv2.morphologyEx(image, cv2.MORPH_DILATE, kernel)
    
    return morphed_image

# Process images in the input folder
for filename in os.listdir(input_folder):
    # Read the image
    image_path = os.path.join(input_folder, filename)
    image = cv2.imread(image_path)

    # Apply image processing steps
    processed_image = grayscale_conversion(image)
    # processed_image = noise_reduction(processed_image)
    processed_image = enhance_contrast(processed_image)
    
    # processed_image = global_thresholding(processed_image)
    # processed_image = adaptive_thresholding(processed_image)
    # processed_image = rotation_correction(processed_image)
    # processed_image = deskew_image(processed_image)
    # processed_image = background_subtraction(processed_image)
    # processed_image = enhance_text_edges(processed_image)
    # processed_image = color_space_transformation(processed_image)
    processed_image = morphological_operations(processed_image)

    # Save the processed image to the output folder
    output_path = os.path.join(output_folder, filename)
    cv2.imwrite(output_path, processed_image)

    print(f'Processed {filename} and saved output to {output_path}')
