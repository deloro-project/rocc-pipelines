#!/usr/bin/env python
"""Exports character annotations on full images into Yolo v5 format."""
import argparse
import logging
import utils.database as db
from utils.filesystem import create_export_structure
from utils.exportutils import export_image, export_yolov5_annotation
from utils.exportutils import save_dataset_description, blur_out_negative_samples
from utils.exportutils import get_cv2_image_size
from utils.yolov5utils import iterate_yolo_directory
from utils.exportutils import move_images_and_labels
from pathlib import Path
import shutil

import cv2 as cv
from sklearn.model_selection import train_test_split

DEBUG_MODE = False
RANDOM_SEED = 2022
TEST_SIZE = 0.2


def get_export_file_names(image_path):
    """Get the names of the export files from original image path.

    Parameters
    ----------
    image_path: str, required
        The path of the original image.

    Returns
    -------
    (image_name, labels_name): tuple of (str, str
        The name of the image to export.
    """
    path = Path(image_path)
    image_name = '{parent}-{image}.png'.format(parent=path.parts[-2],
                                               image=path.stem)
    labels_name = '{parent}-{image}.txt'.format(parent=path.parts[-2],
                                                image=path.stem)
    return image_name, labels_name


def export_annotations(annotations, destination_directory, image_size,
                       binary_read):
    """Export collection of annotations to destination directory.

    Parameters
    ----------
    annotations: iterable of tuples, required
        The collection of annotations to export.
    destination_directory: pathlib.Path, required
        The destination directory.
    image_size: tuple of (int, int), required
        The size of exported images.
    binary_read: bool, required
        Specifies whether to read images in grayscale or color.

    Returns
    -------
    (original_size_dict, labels_map): tuple of (dict of (str, (int, int)), dict of (str, int))
        The original_size_dict maps the exported image names to their original size,
        and labels_map maps labels to their indices.
    """
    original_size_dict, labels_map = {}, {}
    for file_name, letter, *coords in annotations:
        image_name, labels_name = get_export_file_names(file_name)
        if image_name not in original_size_dict:
            image_exported = export_image(
                file_name, str(destination_directory / image_name), image_size,
                binary_read)
            if image_exported:
                img = cv.imread(file_name)
                original_size_dict[image_name] = get_cv2_image_size(img)
            else:
                logging.error("Could not export image {}.".format(file_name))
                continue

        if letter not in labels_map:
            labels_map[letter] = len(labels_map)
        label_index = labels_map[letter]
        x1, y1, x2, y2 = coords
        original_image_size = original_size_dict[image_name]
        export_yolov5_annotation(
            label_index, x1, y1, x2, y2, original_image_size,
            image_size if image_size is not None else original_image_size,
            str(destination_directory / labels_name))
    return original_size_dict, labels_map


def export_char_annotations(args):
    """Export letter annotations under a single label.

    Parameters
    ----------
    args: argparse.Namespace, required
        The parameters specified at command-line. Must have the following attributes:
        - db_server: str - the database server,
        - db_name: str - the database name,
        - user: str - the database user,
        - password: str - the database password,
        - port: int - the port for database server,
        - image_size: int - the size of the exported image in pixels,
        - binary_read: bool - specifies whether to read images in black and white or not,
        - blur_negative_samples: bool - specifies whether to blur negative samples on exported images or not,
        - output_dir: str - the root directory of the export.
    """
    logging.info("Exporting characters in Yolo v5 format.")
    letters_df = db.load_letter_annotations(args.db_server,
                                            args.db_name,
                                            (args.user, args.password),
                                            args.port,
                                            top_labels=None)
    letters_df.letter = 'char'
    logging.info("Creating export directories for letter annotations.")
    staging_dir, train_dir, val_dir, yaml_file = create_export_structure(
        args.output_dir, export_type='characters')

    logging.info("Exporting data to staging directory {}.".format(
        str(staging_dir)))
    image_size_dict, labels_map = export_annotations(letters_df.to_numpy(),
                                                     staging_dir,
                                                     args.image_size,
                                                     args.binary_read)

    if args.blur_negative_samples:
        logging.info("Blurring unmarked letters from all images.")
        blur_verbosity = 11 if DEBUG_MODE else 0
        blur_out_negative_samples(staging_dir,
                                  num_workers=args.blur_workers,
                                  verbosity=blur_verbosity)

    logging.info("Splitting annotations into train/val sets.")
    data = [(img, labels)
            for img, labels in iterate_yolo_directory(staging_dir)]
    train, val = train_test_split(data,
                                  test_size=TEST_SIZE,
                                  random_state=RANDOM_SEED)

    logging.info("Exporting training data.")
    move_images_and_labels(train, staging_dir, train_dir)

    logging.info("Exporting validation data.")
    move_images_and_labels(val, staging_dir, val_dir)

    logging.info("Removing staging directory.")
    shutil.rmtree(staging_dir)

    logging.info(
        "Saving characters dataset description file to {}.".format(yaml_file))
    labels = sorted(labels_map, key=labels_map.get)
    save_dataset_description(str(train_dir), str(val_dir), labels,
                             str(yaml_file))
    logging.info("Finished exporting characters in Yolo v5 format.")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Export annotations on full images for Yolo v5.')
    parser.set_defaults(func=export_char_annotations)

    parser.add_argument('--db-server',
                        help="Name or IP address of the database server.",
                        required=True)

    parser.add_argument('--db-name',
                        help="The name of the database to connect to.",
                        required=True)

    parser.add_argument(
        '--user',
        help="The username under which to connect to the database.",
        required=True)

    parser.add_argument('--password',
                        help="The password of the user.",
                        required=True)

    parser.add_argument(
        '--port',
        help="The port of the database server. Default value is 5432.",
        default="5432")

    parser.add_argument(
        '--output-dir',
        help="The output directory. Default value is './yolo-export'.",
        default='./yolo-export')

    parser.add_argument('--image-size',
                        help="""The size of the exported images.
                        If omitted, the images will be exported in original resolution.""",
                        type=int,
                        nargs=2,
                        default=None)

    parser.add_argument('--binary-read',
                        help="Sample the images as black and white.",
                        action='store_true')
    parser.add_argument(
        '--blur-negative-samples',
        help="Enable blurring of negative samples in the export.",
        action='store_true')

    parser.add_argument(
        '--blur-workers',
        help="Number of images being blurred at the same time. Default is -2.",
        type=int,
        default=-2)

    parser.add_argument(
        '--log-level',
        help="The level of details to print when running.",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO')

    parser.add_argument(
        '--debug',
        help="Enable debug mode to load less data from database.",
        action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=getattr(logging, args.log_level))
    db.DEBUG_MODE = DEBUG_MODE = args.debug
    db.RANDOM_SEED = RANDOM_SEED = 2022
    args.func(args)
    logging.info("That's all folks!")
