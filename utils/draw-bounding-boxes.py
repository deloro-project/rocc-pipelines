#!/usr/bin/env python
"""Utility script to verify if the bounding boxes."""
from argparse import ArgumentParser
from pathlib import Path
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


def iterate_labels(labels_file):
    """Return an iterator over the labels from the specified file.

    Parameters
    ----------
    labels_file: pathlib.Path, required
        The path of the labels file.

    Returns
    -------
    generator of (class_id, center_x, center_y, width, height)
        The label row from the file.
    """
    with open(str(labels_file), 'r') as f:
        for line in f:
            parts = line.split()
            class_id = int(parts[0])
            rectangle = [float(p) for p in parts[1:]]
            yield class_id, *rectangle


def translate_coordinates(center, box_size, image_size):
    """Translate bounding box info into coordinates on image.

    Returns
    (top_left, bottom_down): tuple of points
        The translated coordinates.
    """
    center_x, center_y = center
    box_width, box_height = box_size
    img_width, img_height = image_size

    top_left_x = (center_x - box_width / 2) * img_width
    top_left_y = (center_y - box_height / 2) * img_height

    top_left = (round(top_left_x), round(top_left_y))

    bottom_down_x = top_left_x + box_width * img_width
    bottom_down_y = top_left_y + box_height * img_height
    bottom_right = (round(bottom_down_x), round(bottom_down_y))

    center = (round(center_x * img_width), round(center_y * img_height))

    return top_left, bottom_right, center


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
