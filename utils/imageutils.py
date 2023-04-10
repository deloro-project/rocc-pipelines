"""Utility functions for images."""
import cv2 as cv


def get_cv2_image_size(image):
    """Get image size in (width, height) format from cv2 image.

    Parameters
    ----------
    image: cv2 Image, required
        The image from which to extract size.

    Returns
    -------
    (width, height): tuple of (int, int)
        The size of the image in (width, height) format.
    """
    height, width, *_ = image.shape
    return (width, height)


def read_image_grayscale(image_path: str) -> any:
    """Read an image and convert it to grayscale.

    Parameters
    ----------
    image_path: str, required
        The path of the image.

    Returns
    -------
    image: image
        The contents of the image.
    """
    img = cv.imread(str(image_path))

    # Convert to grayscale.
    grayscale = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # Apply Gaussian blurr.
    blur = cv.GaussianBlur(grayscale, (0, 0), sigmaX=33, sigmaY=33)
    # Divide.
    divide = cv.divide(grayscale, blur, scale=255)
    # OTSU threshold.
    threshold = cv.threshold(divide, 0, 255,
                             cv.THRESH_BINARY + cv.THRESH_OTSU)[1]
    # Apply morphology.
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
    morph = cv.morphologyEx(threshold, cv.MORPH_CLOSE, kernel)
    return morph
