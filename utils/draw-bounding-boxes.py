#!/usr/bin/env python
"""Utility script to verify if the bounding boxes."""
from argparse import ArgumentParser
from pathlib import Path
from yolov5utils import iterate_labels, translate_coordinates
import cv2

COLOR = (255, 0, 0)
THICKNESS = 1


def get_file_paths(args):
    """Return the paths of input image, labels file and output image.

    Parameters
    ----------
    args: argparse.Namespace, required
        The command-line arguments of the script.

    Returns
    -------
    (input_img, labes_file, output_img): tuple of pathlib.Path objects
        The paths of the input image, labels file, and output image.
    """
    input_img = Path(args.input_image)

    if args.labels_file is not None:
        labels_file = Path(args.labels_file)
    else:
        labels_file = input_img.with_suffix('.txt')

    if args.output_image is not None:
        output_img = Path(args.output_image)
    else:
        output_img = Path("{}-out{}".format(input_img.stem, input_img.suffix))

    return input_img, labels_file, output_img


def main(args):
    """Draw bounding boxes on the specified image."""
    input_image, labels_file, output_image = get_file_paths(args)

    out_img = cv2.imread(str(input_image))
    height, width, _ = out_img.shape
    image_shape = (width, height)

    for _, center_x, center_y, box_width, box_height in iterate_labels(
            labels_file):
        top_left, bottom_right, center = translate_coordinates(
            (center_x, center_y), (box_width, box_height), image_shape)

        out_img = cv2.rectangle(out_img, top_left, bottom_right, COLOR,
                                THICKNESS)
        out_img = cv2.circle(out_img, center, 5, COLOR, THICKNESS)
    cv2.imwrite(str(output_image), out_img)


def parse_arguments():
    """Parse command-line arguments."""
    parser = ArgumentParser(
        description='Draw bounding boxes on the specified image.')

    parser.add_argument('--input-image',
                        help="The path of the input image.",
                        required=True,
                        type=str)
    parser.add_argument(
        '--labels-file',
        help="The path of the labels file. Omit if it's near the input image.",
        type=str,
        required=False,
        default=None)
    parser.add_argument('--output-image',
                        help="The path of the output image.",
                        type=str,
                        required=False,
                        default=None)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    main(args)
