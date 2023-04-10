"""Utility functions for images."""


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

