#!/usr/bin/env python
"""Exports letter and line annotations into Yolo v5 format."""
import argparse
import logging
from utils.exportutils import load_annotations, create_directories
from utils.exportutils import export_image, export_yolov5_annotation
from utils.exportutils import save_dataset_description, blur_out_negative_samples
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


def export_collection(annotations, destination_directory, original_size_dict,
                      image_size, labels_map):
    """Export collection of annotations to destination directory.

    Parameters
    ----------
    annotations: iterable of tuples, required
        The collection of annotations to export.
    destination_directory: pathlib.Path, required
        The destination directory.
    original_size_dict: dict of (str, (int, int)), required
        The dict mapping exported image names to their original size.
    image_size: tuple of (int, int), required
        The size of exported images.
    labels_map: dict of (str, int), required
        The dictionary  that maps between a label and its index.
    """
    image_width, image_height = image_size
    for file_name, letter, *coords in annotations:
        image_name, labels_name = get_export_file_names(file_name)
        if image_name not in original_size_dict:
            try:
                export_image(file_name,
                             str(destination_directory / image_name),
                             image_width, image_height)
                img = cv.imread(file_name)
                original_size_dict[image_name] = img.shape
            except (FileNotFoundError, IsADirectoryError):
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


def export_letter_annotations(db_server, db_name, user, password, port,
                              top_labels, image_size, output_dir):
    """Export letter annotations.

    Parameters
    ----------
    db_server: str, required
        The database server.
    db_name: str, required
        The database name.
    user: str, required
        The database user.
    password: str, required
        The database password.
    port: int, required
        The port for database server.
    top_labels: float between 0 and 1, optional
        The top percent of labels to return when ordered descendingly by number of samples.
    image_size: int, required
        The size of the exported image in pixels.
    output_dir: str, required
        The root directory of the export.
    """
    logging.info("Exporting letters in Yolo v5 format.")
    letters_df = load_letter_annotations(db_server, db_name, (user, password),
                                         port, top_labels)
    logging.info("Creating export directories for letter annotations.")
    staging_dir, train_dir, val_dir, yaml_file = create_export_directories(
        output_dir, export_type='letters')

    letter_groups = letters_df.groupby(letters_df.letter)
    image_size_dict = {}
    labels_map = {}
    for letter, group in letter_groups:
        logging.info("Exporting data for label {}.".format(letter))
        ds = group.to_numpy()
        num_samples, _ = ds.shape
        if num_samples < 2:
            logging.warning(
                "There are not enough samples to split for label {}.".format(
                    letter))
            continue

        train, val = train_test_split(ds,
                                      test_size=TEST_SIZE,
                                      random_state=RANDOM_SEED)
        logging.info("Exporting training data.")
        export_collection(train, train_dir, image_size_dict, image_size,
                          labels_map)
        logging.info("Exporting validation data.")
        export_collection(val, val_dir, image_size_dict, image_size,
                          labels_map)
    labels = sorted(labels_map, key=labels_map.get)
    logging.info("Blurring unmarked letters from all images.")
    blur_out_negative_samples(staging_dir, train_dir)
    if not DEBUG_MODE:
        shutil.rmtree(staging_dir)
    logging.info(
        "Saving letters dataset description file to {}.".format(yaml_file))
    save_dataset_description(str(staging_dir), str(val_dir), labels,
                             str(yaml_file))
    logging.info("Finished exporting letters in Yolo v5 format.")


def export_char_annotations(db_server, db_name, user, password, port,
                            image_size, output_dir):
    """Export letter annotations under a single label.

    Parameters
    ----------
    db_server: str, required
        The database server.
    db_name: str, required
        The database name.
    user: str, required
        The database user.
    password: str, required
        The database password.
    port: int, required
        The port for database server.
    image_size: int, required
        The size of the exported image in pixels.
    output_dir: str, required
        The root directory of the export.
    """
    logging.info("Exporting characters in Yolo v5 format.")
    letters_df = load_letter_annotations(db_server,
                                         db_name, (user, password),
                                         port,
                                         top_labels=None)
    letters_df.letter = 'char'
    logging.info("Creating export directories for letter annotations.")
    staging_dir, train_dir, val_dir, yaml_file = create_export_directories(
        output_dir, export_type='characters')
    image_size_dict, labels_map = {}, {}
    train, val = train_test_split(letters_df.to_numpy(),
                                  test_size=TEST_SIZE,
                                  random_state=RANDOM_SEED)

    logging.info("Exporting training data.")
    export_collection(train, staging_dir, image_size_dict, image_size,
                      labels_map)
    logging.info("Blurring unmarked letters from all images.")
    blur_out_negative_samples(staging_dir, train_dir)
    if not DEBUG_MODE:
        shutil.rmtree(staging_dir)

    logging.info("Exporting validation data.")
    export_collection(val, val_dir, image_size_dict, image_size, labels_map)
    labels = sorted(labels_map, key=labels_map.get)

    logging.info(
        "Saving characters dataset description file to {}.".format(yaml_file))
    save_dataset_description(str(train_dir), str(val_dir), labels,
                             str(yaml_file))
    logging.info("Finished exporting characters in Yolo v5 format.")


def main(args):
    """Export annotations in Yolo v5 format.

    Parameters
    ----------
    args: argparse.Namespace, required
        The arguments of the script.
    """
    export_letter_annotations(args.db_server, args.db_name, args.user,
                              args.password, args.port, args.top_labels,
                              args.image_size, args.output_dir)
    export_char_annotations(args.db_server, args.db_name, args.user,
                            args.password, args.port, args.image_size,
                            args.output_dir)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Export annotations for Yolo v5.')
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

    parser.add_argument('--top-labels',
                        help="Percentage of top labels to export.",
                        type=float,
                        default=0.1)
    parser.add_argument(
        '--output-dir',
        help="The output directory. Default value is './yolo-export'.",
        default='./yolo-export')
    parser.add_argument(
        '--image-size',
        help="The size of the exported images. Default is [1024, 768].",
        type=int,
        nargs=2,
        default=[1280, 1280])
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
    DEBUG_MODE = args.debug
    main(args)
    logging.info("That's all folks!")
