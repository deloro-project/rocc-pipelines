#!/usr/bin/env python
"""Script for preparing Yolo v5 character detection results for classification."""
from argparse import ArgumentParser
import logging
from pathlib import Path
import pandas as pd
from typing import Tuple
from yolov5utils import translate_coordinates
import cv2 as cv


def create_output_directory(parent_dir: str, image_name: str) -> Path:
    """Create the directory structure for the output.

    Parameters
    ----------
    parent_dir: str, required
        The path of the parent output directory.
    image_name: str, required
        The name of the image without extension.

    Returns
    -------
    output_directory: Path
        The path of the output directory.
    """
    parent = Path(parent_dir)
    child = parent / image_name
    child.mkdir(exist_ok=True, parents=True)
    return child


def iterate_inputs(images_dir: str,
                   labels_dir: str) -> Tuple[Path, pd.DataFrame]:
    """Iterate over input directories and return images with detected letters.

    Parameters
    ----------
    images_dir: str, required
        The path of the images directory.
    labels_dir: str, required
        The path of the Yolo v5 labels output.

    Returns
    -------
    (image_path, characters): tuple of (Path, pandas.DataFrame)
        The path of the image and the data frame containing detected letters.
    """
    img_dir, lbl_dir = Path(images_dir), Path(labels_dir)
    images, labels = {}, {}
    for image in img_dir.glob('*.*'):
        images[image.stem] = image
    for labels_file in lbl_dir.glob('*.txt'):
        labels[labels_file.stem] = str(labels_file)

    for stem, file_path in labels.items():
        if stem not in images:
            continue

        image_path = images[stem]
        df = pd.read_csv(file_path,
                         delimiter=' ',
                         names=[
                             'label', 'x_center', 'y_center', 'width',
                             'height', 'confidence'
                         ])
        yield image_path, df


def export_cutouts_for_classification(image_path: Path,
                                      coordinates: pd.DataFrame,
                                      output_dir: Path):
    """Export detected letters for classification.

    Parameters
    ----------
    image_path: Path, required
        The path of the image from which to cut letters.
    coordinates: pandas.DataFrame, required
        The data frame containing coordinates of detected letters in Yolo v5 format.
    output_dir: Path, required
        The path of the output directory.
    """
    img = cv.imread(str(image_path))
    for row in coordinates.itertuples(index=False):
        center = (row.x_center, row.y_center)
        box_size = (row.width, row.height)
        img_height, img_width, _ = img.shape
        image_size = (img_width, img_height)
        top_left, bottom_right, _ = translate_coordinates(
            center, box_size, image_size)
        x, y = top_left
        x_max, y_max = bottom_right
        letter = img[y:y_max, x:x_max, ]
        name = "{}-{}-{}-{}.png".format(x, y, x_max, y_max)
        cv.imwrite(str(output_dir / name), letter)


def parse_arguments():
    """Parse command-line arguments."""
    parser = ArgumentParser(description="""
        Prepare Yolo v5 character detection results for classification.""")
    parser.add_argument('--images-dir',
                        help="The path of the images directory.",
                        default='./images')
    parser.add_argument('--labels-dir',
                        help="The path of the labels directory.",
                        default='./labels')
    parser.add_argument('--output-dir',
                        help="The path of the output directory.",
                        default='./output')
    parser.add_argument(
        '--log-level',
        help="The level of details to print when running.",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO')
    return parser.parse_args()


def main(args):
    """Prepare results for classification."""
    for img_path, coordinates in iterate_inputs(args.images_dir,
                                                args.labels_dir):
        logging.info("Exporting detected letters from %s.", str(img_path))
        output_dir = create_output_directory(args.output_dir, img_path.stem)
        export_cutouts_for_classification(img_path, coordinates, output_dir)
    logging.info("That's all folks!")


if __name__ == '__main__':
    args = parse_arguments()
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=getattr(logging, args.log_level))
    main(args)
