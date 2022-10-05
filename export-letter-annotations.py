#!/usr/bin/env python
"""Exports letter annotations for training the letter classifier."""
import argparse
import logging
import cv2 as cv
import shutil
from pathlib import Path
from pandas import DataFrame
from typing import Iterable
from sklearn.model_selection import train_test_split
import utils.database as db
from utils.filesystem import create_export_structure

RANDOM_SEED = 2022
TEST_SIZE = 0.2


def read_image(image_path: str) -> any:
    """Read the image from the specified path and apply transformations.

    Parameters
    ----------
    image_path: str, required
        The path of the image to read.

    Returns
    -------
    img: Image
        The image after being transformed; `None` if image doesn't exist.
    """
    img = cv.imread(image_path)
    if img is None:
        logging.error("Could not read image %s.", image_path)
        return None

    # Convert to grayscale.
    grayscale = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    return grayscale


def load_letters(db_server: str, db_name: str, user_name: str, password: str,
                 min_samples: int) -> DataFrame:
    """Load letters from the database and filter on number of samples.

    Parameters
    ----------
    db_server : str, required
        The name or IP address of the database server.
    db_name : str, required
        The name of the database containing annotations.
    user_name : str, required
        The username which is allowed to connect to the database.
    password : str, required
        The password of the username.
    min_samples: int, required
        The minimum number of samples a letter must have in order to be included in the export.

    Returns
    -------
    letters: pandas.DataFrame
        The DataFrame containing letter annotations.
    """
    df, _ = db.load_annotations(db_server, db_name, user_name, password)
    # Remove samples labeled wth '#'
    df = df[df.letter != '#']
    # Remove samples with less than min occurrences
    df = df.groupby(df.letter).filter(lambda grp: len(grp) >= min_samples)
    # Remove non-letter samples
    df = df[df.letter.str.isalpha()]
    return df


def export_annotation_cutouts(annotations: DataFrame,
                              staging_dir: Path) -> DataFrame:
    """Export annotation cutouts to staging directory.

    Parameters
    ----------
    annotations: pandas.DataFrame, required
        The data frame containing letter annotations.
    staging_dir: pathlib.Path, required
        The path of the staging directory.

    Returns
    -------
    letters: pandas.DataFrame
        A data frame containing labels and file names of exported cutouts.
    """
    page_file_name = None
    letters = {'letter': [], 'file_name': []}
    for row in annotations.itertuples():
        if page_file_name != row.page_file_name:
            page_file_name = row.page_file_name
            logging.info("Exporting letter annotations from %s.",
                         page_file_name)
            img = read_image(page_file_name)
        if img is None:
            continue

        x, y = int(row.left_up_horiz), int(row.left_up_vert)
        w, h = int(row.right_down_horiz), int(row.right_down_vert)
        char_frame = img[y:h, x:w, ]
        if 0 in char_frame.shape:
            logging.error(
                "Invalid values for bounding box of image %s: [%s, %s, %s, %s].",
                row.letter_id, row.left_up_horiz, row.left_up_vert,
                row.right_down_horiz, row.right_down_vert)
            continue

        file_name = str(staging_dir / "{}.png".format(row.letter_id))
        cv.imwrite(file_name, char_frame)
        letters['letter'].append(row.letter)
        letters['file_name'].append(file_name)

    return DataFrame.from_dict(letters)


def get_num_instances_to_sample(cutouts: DataFrame) -> int:
    """Compute number of instances to sample for each letter.

    Parameters
    ----------
    cutouts: pandas.DataFrame, required
        The data frame containing labels and file names of letter cutouts.

    Returns
    -------
    num_instances: int
        The size of the smallest group of file names for each letter.
    """
    gr = cutouts.groupby(cutouts.letter).count()
    num_instances = gr.sort_values(by='file_name', ascending=True).min()[0]
    return num_instances


def move_to_target_directory(files: Iterable[str], directory: Path):
    """Move the specified files to target directory.

    Parameters
    ----------
    files: iterable of str, required
        The collection of files to move.
    directory: Path, required
        The target directory.
    """
    if not directory.exists():
        logging.info("Creating directory %s.", str(directory))
        directory.mkdir(parents=True, exist_ok=True)

    for f in files:
        file_path = Path(f)
        file_path.rename(directory / file_path.name)


def export_letter_annotations(args):
    """Export letter annotations for classification training.

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
        - output_dir: str - the root directory of the export.
    """
    df = load_letters(args.db_server, args.db_name, args.user, args.password,
                      args.min_samples_per_class)
    df.sort_values(by='page_file_name', inplace=True)
    staging_dir, train_dir, val_dir, _ = create_export_structure(
        args.output_dir, export_type='letters')
    df = export_annotation_cutouts(df, staging_dir)
    num_instances = get_num_instances_to_sample(df)
    for letter in df.letter.unique():
        sample = df[df.letter == letter].sample(n=num_instances,
                                                random_state=RANDOM_SEED)
        train, test = train_test_split([f for f in sample.file_name],
                                       test_size=TEST_SIZE,
                                       random_state=RANDOM_SEED)
        move_to_target_directory(train, train_dir / letter)
        move_to_target_directory(test, val_dir / letter)
    logging.info("Removing staging directory %s.", str(staging_dir))
    shutil.rmtree(staging_dir)
    logging.info("That's all folks!")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Export annotations on full images for Yolo v5.')
    parser.set_defaults(func=export_letter_annotations)

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
        '--output-dir',
        help="The output directory. Default value is './yolo-export'.",
        default='./yolo-export')

    parser.add_argument(
        '--min-samples-per-class',
        help="Export class only if there are a minimum number of samples.",
        type=int,
        default=1000)

    parser.add_argument(
        '--log-level',
        help="The level of details to print when running.",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=getattr(logging, args.log_level))
    args.func(args)
