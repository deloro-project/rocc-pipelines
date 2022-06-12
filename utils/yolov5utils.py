# -*- coding: utf-8 -*-
"""Utility functions for Yolo v5."""
import logging


def iterate_labels(labels_file):
    """Return an iterator over the labels from the specified file.

    Parameters
    ----------
    labels_file: pathlib.Path, required
        The path of the labels file.

    Returns
    -------
    generator of (class_id, center_x, center_y, width, height)
        The label row from the file.
    """
    with open(str(labels_file), 'r') as f:
        for line in f:
            parts = line.split()
            class_id = int(parts[0])
            rectangle = [float(p) for p in parts[1:]]
            yield class_id, *rectangle


def translate_coordinates(center, box_size, image_size):
    """Translate bounding box info into coordinates on image.

    Returns
    (top_left, bottom_down): tuple of points
        The translated coordinates.
    """
    center_x, center_y = center
    box_width, box_height = box_size
    img_width, img_height = image_size

    top_left_x = (center_x - box_width / 2) * img_width
    top_left_y = (center_y - box_height / 2) * img_height

    top_left = (round(top_left_x), round(top_left_y))

    bottom_down_x = top_left_x + box_width * img_width
    bottom_down_y = top_left_y + box_height * img_height
    bottom_right = (round(bottom_down_x), round(bottom_down_y))

    center = (round(center_x * img_width), round(center_y * img_height))

    return top_left, bottom_right, center


def iterate_yolo_directory(directory_path, image_extension='.png'):
    """Iterate over files in a given directory and return pairs of image and labels file.

    Parameters
    ----------
    directory_path: pathlib.Path, required
        The path of the directory to iterate.
    image_extension: str, optional
        The extension of the images to process. Default is .png.

    Returns
    -------
    iterator of (image, labels_file): iterator of tuple of (str, str)
        The pairs of image file and associated labels file.
    """
    for image_file in directory_path.glob("*{}".format(image_extension)):
        labels_file = image_file.with_suffix('.txt')
        if not labels_file.exists():
            logging.warning(
                "Could not find labels file for image {}.".format(image_file))
            continue
        yield str(image_file), str(labels_file)
