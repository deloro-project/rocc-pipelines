#!/usr/bin/env python
"""Utility functions for annotations export."""
import logging
from sqlalchemy import create_engine
import pandas as pd
from PIL import Image


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
    original_width, original_height = original_size
    export_width, export_height = export_size
    x_scale = export_width / original_width
    y_scale = export_height / original_height
    x_old, y_old = point
    x_new = x_old * x_scale
    y_new = y_old * y_scale
    return (round(x_new), round(y_new))


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
    center, dimmensions = calculate_bounding_box(top_left, bottom_right,
                                                 export_image_size)
    x, y = center
    w, h = dimmensions
    with open(labels_file, 'a') as f:
        f.write("{label} {x} {y} {w} {h}".format(label=label_index,
                                                 x=x,
                                                 y=y,
                                                 w=w,
                                                 h=h))
        f.write("\n")


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
