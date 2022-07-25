#!/usr/bin/env python
"""Resize images to specified size."""
import logging
from argparse import ArgumentParser
import cv2 as cv
from pathlib import Path


def iterate_files(directory, images):
    """Iterate over files from either the specified directory or iterable of images.

    Parameters
    ----------
    directory: str, required
        The path of the directory to iterate images from.
    images: iterable of str, required
        The paths of individual images to iterate.

    Returns
    -------
    generator: generator of pathlib.Path
        The paths of images.
    """
    if directory is not None:
        for file_name in Path(directory).glob("*.*"):
            yield file_name

    if images is not None:
        for file_name in images:
            yield Path(file_name)


def resize_image(file_name, size):
    """Resize the image to specified size (size x size pixels).

    Parameters
    ----------
    file_name: str, required
        The image to resize.
    size: int, required
        The size of the new image.
    """
    logging.info("Resizing {image} to {size}x{size} pixels".format(
        image=file_name, size=size))

    img = cv.imread(file_name, cv.IMREAD_COLOR)
    resized = cv.resize(img, (size, size))
    cv.imwrite(file_name, resized)


def parse_arguments():
    """Parse command-line arguments.

    Returns
    -------
    args: argparse.Namespace
        The command-line arguments.
    """
    parser = ArgumentParser(description='Resize images.')

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--directory',
        help="The path of the directory containin images to resize.",
        type=str)
    group.add_argument('--images',
                       help="The images to resize.",
                       type=str,
                       nargs='+')
    parser.add_argument('--image-size',
                        help="The image size.",
                        required=True,
                        type=int)

    parser.add_argument(
        '--log-level',
        help="The level of details to print when running.",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO')
    return parser.parse_args()


def main(args):
    """Resize the images specified by command-line arguments.

    Parameters
    ----------
    args: argparse.Namespace, required
        The command-line arguments provided to the script.
    """
    for file_path in iterate_files(args.directory, args.images):
        resize_image(str(file_path), args.image_size)


if __name__ == '__main__':
    args = parse_arguments()
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=getattr(logging, args.log_level))
    main(args)
