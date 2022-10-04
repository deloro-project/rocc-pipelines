#!/usr/bin/env python
"""Exports letter annotations for training the letter classifier."""
import argparse
import logging
import cv2 as cv
from pandas import DataFrame
import utils.database as db
from utils.filesystem import create_export_structure


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
    print(df.columns)
    page_file_name = None
    for row in df.itertuples():
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

        cv.imwrite(str(staging_dir / "{}.png".format(row.letter_id)),
                   char_frame)
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
    db.DEBUG_MODE = args.debug
    db.RANDOM_SEED = 2022
    args.func(args)
