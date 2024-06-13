import cv2
import numpy as np


class ImageEnhancer:

    def __init__(self):
        pass

    # Function to apply grayscale conversion to an image
    def grayscale_conversion(self, image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray_image

    # Function to apply noise reduction or removal (blur)
    def noise_reduction(self, image):
        # blurred_image = cv2.bilateralFilter(image, 15, 65, 65)
        denoised_image = cv2.fastNlMeansDenoising(
            image, None, h=10, templateWindowSize=7, searchWindowSize=21)
        return denoised_image

    # Function to enhance image contrast
    def enhance_contrast(self, image):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        equalized_image = clahe.apply(image)
        return equalized_image

    def sharpen_image(self, image):
        kernel = np.array([[-1, -1, -1],
                           [-1, 9, -1],
                           [-1, -1, -1]])
        sharpened_image = cv2.filter2D(image, -1, kernel)
        return sharpened_image

    # Function to apply adaptive thresholding
    def global_thresholding(self, image):
        _, thresholded_image = cv2.threshold(
            image, 140, 255, cv2.THRESH_BINARY)
        return thresholded_image

    # Function to apply adaptive thresholding
    def adaptive_thresholding(self, image):
        thresholded_image = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return thresholded_image

    def dilate_and_erode(self, image):
        kernel = np.ones((1, 1), np.uint8)
        img = cv2.dilate(image, kernel, iterations=1)
        img = cv2.erode(img, kernel, iterations=1)
        return img

    # Perform morphological opening to enhance text edges
    def enhance_text_edges(self, image):
        kernel = np.ones((3, 3), np.uint8)
        opened = cv2.morphologyEx(image, cv2.MORPH_DILATE, kernel)
        edges = cv2.absdiff(opened, image)
        inverted_edges = 255 - edges
        return inverted_edges

    # Perform Canny edge detection
    def enhance_text_edges_canny(self, image):
        blurred_image = cv2.GaussianBlur(image, (3, 3), 0)
        edges = cv2.Canny(blurred_image, 100, 200)
        inverted_edges = 255 - edges
        return inverted_edges

    # Function to perform morphological operations
    def morphological_operations(self, image):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morphed_image = cv2.morphologyEx(image, cv2.MORPH_DILATE, kernel)
        return morphed_image
