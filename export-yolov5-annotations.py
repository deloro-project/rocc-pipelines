#!/usr/bin/env python
"""Exports character annotations into Yolo v5 format."""
import argparse
import logging
from utils.exportutils import load_annotations, create_directories
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


def filter_letter_annotations(letters_df, top_size):
    """Filter letter annotations by top number of samples.

    Parameters
    ----------
    letters_df: pandas.DataFrame, required
        The dataframe containing letter annotations.
    top_size: float, required
        The percent of top labels to return sorted by size.

    Returns
    -------
    letters_df: pandas.DataFrame
        The filtered dataframe.
    """
    logging.info("Filtering letter annotations to top {} percent.".format(
        top_size * 100))
    labels = list(letters_df.letter.unique())
    _, x = train_test_split(labels,
                            test_size=top_size,
                            random_state=RANDOM_SEED)
    letter_groups = letters_df.groupby(
        letters_df.letter)['letter'].count().nlargest(len(x))
    letter_groups = list(letter_groups.index)
    logging.info("Only the following labels will be exported: {}.".format(
        ', '.join(letter_groups)))
    return letters_df[letters_df.letter.map(lambda l: l in letter_groups)]


def load_letter_annotations(db_server,
                            db_name,
                            credentials,
                            port,
                            top_labels=None):
    """Load letter annotations from database and optionally filters the ones with higher number of samples.

    Parameters
    ----------
    db_server: str, required
        The database server.
    db_name: str, required
        The database name.
    credentials: tuple of (str, str), required
        The user name and password for connecting to the database.
    port: int, required
        The port for database server.
    top_labels: float between 0 and 1, optional
        The top percent of labels to return when ordered descendingly by number of samples.
        Default is None; when 0 or None returns all labels.

    Returns
    -------
    letters_df: pandas.DataFrame
        The dataframe containing letter annotations.
    """
    user, password = credentials
    letters_df, _ = load_annotations(db_server, db_name, user, password, port)
    letters_df = letters_df[[
        'page_file_name', 'letter', 'left_up_horiz', 'left_up_vert',
        'right_down_horiz', 'right_down_vert'
    ]]

    if DEBUG_MODE:
        logging.info(
            "Running in debug mode; database results are truncated to 100 rows."
        )
        letters_df = letters_df.head(100)

    if top_labels:
        return filter_letter_annotations(letters_df, top_labels)

    return letters_df


def create_export_directories(output_directory, export_type):
    """Create directory structure for export.

    Parameters
    ----------
    output_directory: str, required
        The root directory where export data will reside.
    export_type: str, required
        The type of export; can be either 'letters', 'characters', or 'lines'.
        Default is 'letters'.

    Returns
    -------
    (train_dir, val_dir, yaml_file): tuple of pathlib.Path
        The directories for training data, validation data,
        and path of the dataset description file respectively.
    """
    export_dir = Path(args.output_dir) / export_type
    staging_dir = export_dir / 'staging_dir'
    train_dir = export_dir / 'train'
    val_dir = export_dir / 'val'
    yaml_file = export_dir / '{}.yaml'.format(export_type)
    create_directories(staging_dir, train_dir, val_dir)
    return staging_dir, train_dir, val_dir, yaml_file


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
    image_width, image_height = image_size
    for file_name, letter, *coords in annotations:
        image_name, labels_name = get_export_file_names(file_name)
        if image_name not in original_size_dict:
            image_exported = export_image(
                file_name, str(destination_directory / image_name),
                image_width, image_height, binary_read)
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
        export_yolov5_annotation(label_index, x1, y1, x2, y2,
                                 original_image_size, image_size,
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
        - output_dir: str - the root directory of the export.
    """
    logging.info("Exporting characters in Yolo v5 format.")
    letters_df = load_letter_annotations(args.db_server,
                                         args.db_name,
                                         (args.user, args.password),
                                         args.port,
                                         top_labels=None)
    letters_df.letter = 'char'
    logging.info("Creating export directories for letter annotations.")
    staging_dir, train_dir, val_dir, yaml_file = create_export_directories(
        args.output_dir, export_type='characters')

    logging.info("Exporting data to staging directory {}.".format(
        str(staging_dir)))
    image_size_dict, labels_map = export_annotations(letters_df.to_numpy(),
                                                     staging_dir,
                                                     args.image_size,
                                                     args.binary_read)

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


def add_common_arguments(parser):
    """Add common argument to the argument parrser.

    Parameters
    ----------
    parser: argparse.ArgumentParser, required
        The parser to which to add the arguments.
    """
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

    parser.add_argument(
        '--image-size',
        help="The size of the exported images. Default is [1024, 768].",
        type=int,
        nargs=2,
        default=[1024, 786])

    parser.add_argument('--binary-read',
                        help="Sample the images as black and white.",
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


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Export annotations for Yolo v5.')
    subparsers = parser.add_subparsers()

    characters = subparsers.add_parser(
        'characters', help="Export character annotations for Yolo v5.")
    characters.set_defaults(func=export_char_annotations)
    add_common_arguments(characters)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=getattr(logging, args.log_level))
    DEBUG_MODE = args.debug
    args.func(args)
    logging.info("That's all folks!")
