#!/usr/bin/env python
"""Utility functions for annotations export."""
import logging

import numpy as np
from sqlalchemy import create_engine
import pandas as pd
import cv2 as cv
from PIL import Image
from io import StringIO
from pathlib import Path
from utils.yolov5utils import iterate_labels, translate_coordinates, iterate_yolo_directory


def load_annotations(server, database, user, password, port=5432):
    """Load the annotations from a PostgreSQL database into a padans DataFrame.

    Parameters
    ----------
    server : str, required
        The name or IP address of the database server.
    database : str, required
        The name of the database containing annotations.
    user : str, required
        The username which is allowed to connect to the database.
    password : str, required
        The password of the username.
    port : str, optional
        The port for connecting to the database.

    Returns
    -------
    (letters_df, lines_df) : tuple of pandas.DataFrame
        Dataframes containing all the annotations.
    """
    logging.info("Loading annotations from database...")
    template = 'postgresql://{user}:{password}@{server}:{port}/{database}'
    conn_str = template.format(user=user,
                               password=password,
                               server=server,
                               port=port,
                               database=database)

    engine = create_engine(conn_str)
    with engine.connect() as conn:
        letters_df = pd.read_sql('select * from letter_annotations', conn)
        lines_df = pd.read_sql('select * from line_annotations', conn)

    num_rows, _ = letters_df.shape
    logging.info(
        "Finished loading {} letter annotations from database.".format(
            num_rows))
    num_rows, _ = lines_df.shape
    logging.info("Finished loading {} lines annotations from database.".format(
        num_rows))
    return letters_df, lines_df


def create_directories(*paths):
    """Create directory structure for the specified path.

    Parameters
    ----------
    paths: tuple of pathlib.Path, required
        The paths for which to create directories.
    """
    for path in paths:
        if path.exists():
            logging.info("Path {} already exists.".format(str(path)))
            continue

        logging.info("Creating directory {}.".format(str(path)))
        path.mkdir(parents=True, exist_ok=True)


def scale_point(point, original_size, export_size):
    """Scale the given point from the original image size to the exported image size.

    Parameters
    ----------
    point: tuple of (int, int), required
        The point to scale.
    original_size: tuple of (int, int), required
        The size in pixels (w, h) of the original image.
    export_size: tuple of (int, int), required
        The size in pixels (w, h) of the exported (resized) image.

    Returns
    -------
    scaled_point: tuple of (int, int)
        The point scaled from original image size to exported image size.
    """
    original_height, original_width, _ = original_size
    export_width, export_height = export_size
    x_scale = export_width / original_width
    y_scale = export_height / original_height
    x_old, y_old = point
    x_new = x_old * x_scale
    y_new = y_old * y_scale
    return round(x_new), round(y_new)


def calculate_bounding_box(top_left, bottom_right, image_size):
    """Calculate the center point and dimensions of the bounding box.

    Parameters
    ----------
    top_left: tuple of (number, number), required
        The (x, y) coordinates of the top-left point.
    bottom_right: tuple of (number, number), required
        The (x, y) coordinates of the bottom-right point.
    image_size: tuple of (number, number), required
        The size of the image (width, height).

    Returns
    -------
    (center, dimensions): tuple of (center point coordinates, dimensions of the rectangle)
        The coordinates of center point (x, y), and dimensions (width, height) of the bounding box.
    """
    x1, y1 = top_left
    x2, y2 = bottom_right
    width, height = image_size

    x_center = x1 + (x2 - x1) / 2
    y_center = y1 + (y2 - y1) / 2
    x_center = x_center / width
    y_center = y_center / height

    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height

    return (x_center, y_center), (box_width, box_height)


def export_yolov5_annotation(label_index, left_up_horiz, left_up_vert,
                             right_down_horiz, right_down_vert,
                             original_image_size, export_image_size,
                             labels_file):
    """Export annotation in Yolo v5 format to the labels file.

    Parameters
    ----------
    label_index: int, required
        The label index.
    left_up_horiz: number, required
        Coordinate of the top-left point on the X scale.
    left_up_vert: number, required
        Coordinate of the top-left point in the Y scale.
    right_down_horiz: number, required
        Coordinate of the bottom-right point on the X scale.
    right_down_vert: number, required
        Coordinate of the bottom-right point in the Y scale.
    original_image_size: tuple of (int, int), required
        The size in pixels (w, h) of the original image.
    export_image_size: tule of (int, int), required
        The size in pixels (w, h) of the exported (resized) image.
    labels_file: str, required
        The path of the file containing labels.
    """
    point = (left_up_horiz, left_up_vert)
    top_left = scale_point(point, original_image_size, export_image_size)
    point = (right_down_horiz, right_down_vert)
    bottom_right = scale_point(point, original_image_size, export_image_size)
    center, dimensions = calculate_bounding_box(top_left, bottom_right,
                                                export_image_size)
    x, y = center
    w, h = dimensions
    with open(labels_file, 'a') as f:
        f.write("{label} {x} {y} {w} {h}".format(label=label_index,
                                                 x=x,
                                                 y=y,
                                                 w=w,
                                                 h=h))
        f.write("\n")


def create_mask(top_left_corner, bottom_right_corner, img_size):
    """Create a mask that will cover the text on the image.

    This method will create a mask which will be an image with a black background and white coloring for the zone witch
    should contain the text. We take the coords of the text zone, add some padding to make sure its mostly covered and
    make it white.

    Parameters
    ----------
    top_left_corner: tuple of (int, int), required
        The coordinates of the top-left corner of the mask.
    bottom_right_corner: tuple of (int, int), required
        The coordinates of the bottom-right corner of the mask.
    img_size: tuple of (int, int), required
        The size of the image in (width, height) format.

    Returns
    -------
    mask: image
        The mask image.
    """
    x1, y1 = top_left_corner
    x2, y2 = bottom_right_corner
    img_width, img_height = img_size
    mask = np.empty([img_height, img_width])
    mask.fill(0)
    mask[y1:y2, x1:x2] = 255
    cv.imwrite("mask.png", mask)
    return cv.imread("mask.png", cv.IMREAD_GRAYSCALE)


def eliminate_all_letters_from_image(img, mask, radius=10):
    """Eliminate all letters from image by applying the provided mask.

    Parameters
    ----------
    img: image, required
        The unaltered image to which to apply the mask.
    mask: image, required
        Mask that specifies the zone which will be eliminated.
    radius: int, optional
        Radius of a circular neighborhood of each point inpainted that is considered by the CV2 algorithm.

    Returns
    -------
    image which does not contain anymore text
    """
    return cv.inpaint(img, mask, radius, flags=cv.INPAINT_TELEA)


def put_letters_back(img, letters):
    """Draw annotated letters over the masked image.

    Parameters
    ----------
    img: image, required
        Image that has all letters removed.
    letters: iterable of boxes of annotated letters and their coordinates
        Original boxes that need to be placed back on their initial coordinates.

    Returns
    -------
    painted: image
        The image where annotated letters have been restored to their position.
    """
    for letter_img, top_left, bottom_right in letters:
        x1, y1 = top_left
        x2, y2 = bottom_right
        img[y1:y2, x1:x2] = letter_img
    return img


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
    height, width, _ = image.shape
    return (width, height)


def get_mask_coordinates(image_size):
    """Determine the coordinates of the mask from the coordinates of the annotations and image size.

    Parameters
    ----------
    image_size: tuple of (int, int), required
        The size of the image in (width, height) format.

    Returns
    -------
    min_top_left, max_bottom_right: tuple of (point, point)
        The minimum point on the top left, and the maximum point on the bottom right from annotations.
    """
    width, height = image_size
    return (30, 30), (width - 30, height - 30)


def get_path_for_move(file_name, target_dir):
    """Get the path as if file was moved into target directory.

    Parameters
    ----------
    file_name: str, required
        The file to be moved.
    target_dir: pathlib.Path
        The directory where the file is to be moved.

    Returns
    -------
    target_file: pathlib.Path
        New path representing the file being moved to target directory.
    """
    file_path = Path(file_name)
    return target_dir / file_path.name


def blur_out_negative_samples(staging_dir, train_dir):
    """Apply a blur mask on the unannotated letters in the images.

    Parameters
    ----------
    staging_dir: pathlib.Path, required
        Directory containing original, resized images.
    train_dir: pathlib.Path, required
        Directory where we copy the images after being cleaned of negative samples
    """
    for img_file, labels_file in iterate_yolo_directory(staging_dir):
        logging.info("Blurring out negative samples from {}.".format(img_file))
        letters = []
        img = cv.imread(img_file)
        img_size = get_cv2_image_size(img)
        for _, x, y, width, height in iterate_labels(labels_file):
            center, box_size = (x, y), (width, height)
            (x1, y1), (x2,
                       y2), _ = translate_coordinates(center, box_size,
                                                      img_size)
            letters.append((img[y1:y2, x1:x2].copy(), (x1, y1), (x2, y2)))
        min_top_left, max_bottom_right = get_mask_coordinates(img_size)
        mask = create_mask(min_top_left, max_bottom_right, img_size)
        img = eliminate_all_letters_from_image(img, mask)
        img = put_letters_back(img, letters)
        train_image_path = get_path_for_move(img_file, train_dir)
        cv.imwrite(str(train_image_path), img)
        labels = Path(labels_file)
        labels = labels.rename(get_path_for_move(labels_file, train_dir))


def export_image(src_path, dest_path, width, height):
    """Export and resize the image.

    Parameters
    ----------
    src_path: str, required
        The source path of the image.
    dest_path: str, required
        The destination path of the image.
    width: int, required
        Width of the exported image.
    height: int, required
        Height of the exported image.
    """
    logging.info("Exporting image {} to {}.".format(src_path, dest_path))
    with Image.open(src_path) as source:
        destination = source.resize((width, height))
        destination.save(dest_path)
        destination.close()


def save_dataset_description(train, val, labels, yaml_file):
    """Save dataset description to YAML file.

    Parameters
    ----------
    train: str, required
        The path to the training directory.
    val: str, required
        The path to the validation directory.
    labels: list of str, required
        The list of class labels.
    yaml_file: str, required
        The path of the output YAML file.
    """
    # Hack: PyYaml does not quote the label names; as such
    # we have to print the labels and pass the resulting string
    with StringIO() as output:
        print(labels, file=output)
        names = output.getvalue()

    yaml_content = """# Data directories
train: {train}
val: {val}

# Number of classes
nc: {nc}

# Label names
names: {names}
"""

    with open(yaml_file, 'w') as f:
        f.write(
            yaml_content.format(train=train,
                                val=val,
                                nc=len(labels),
                                names=names))
