#!/usr/bin/env python
"""Export window cutouts from images."""
import logging
from argparse import ArgumentParser, Namespace
import cv2 as cv

from pathlib import Path
import pandas as pd
from typing import List, Generator
from collections import namedtuple
from utils.imageutils import read_image_grayscale, get_cv2_image_size

SlidingWindow = namedtuple('SlidingWindow', ['start', 'end'])
WindowCoordinates = namedtuple(
    'WindowCoordinates',
    ['top_left_x', 'top_left_y', 'bottom_right_x', 'bottom_right_y'])
WindowMetadata = namedtuple('WindowMetadata', [
    'image_width', 'image_height', 'window_name', 'window_size', 'top_left_x',
    'top_left_y', 'bottom_right_x', 'bottom_right_y'
])


def calculate_sliding_windows(window_size: int, stride: int,
                              limit: int) -> List[SlidingWindow]:
    """Calculate the sliding windows for the specified size and stride.

    Parameters
    ----------
    window_size: int, required
        The size of the sliding window.
    stride: int, required
        The stride of the sliding window (how many units to move the window forward).
    limit: int, required
        The upper limit of the window.

    Returns
    -------
    windows: list of SlidingWindow
        The list of sliding windows.
    """
    index, windows = 0, []
    left_window, right_window = SlidingWindow(0, 0), SlidingWindow(0, 0)
    while (left_window.end <= limit / 2):
        left_window = SlidingWindow(index * stride,
                                    index * stride + window_size)
        windows.append(left_window)
        right_window = SlidingWindow(limit - index * stride - window_size,
                                     limit - index * stride)
        windows.append(right_window)
        index += 1

    return list(sorted(windows, key=lambda window: window.start))


def calculate_window_coordinates(
        image_width: int,
        image_height: int,
        window_size: int,
        horizontal_stride: int = 140,
        vertical_stride: int = 160) -> List[WindowCoordinates]:
    """Calculate the coordinates of the windows.

    Parameters
    ----------
    image_width: int, required
        The width of the image.
    image_height: int, required
        The height of the image.
    window_size: int, required
        The size of the window.
    horizontal_stride: int, optional
        The number of units to move the window horizontally.
        Default value is 140.
    vertical_stride: int, optional
        The number of units to move the window vertically.

    Returns
    -------
    windows: list of Window tuples
        The list of window coordinates.
    """
    for v_window in calculate_sliding_windows(window_size, vertical_stride,
                                              image_height):
        for h_window in calculate_sliding_windows(window_size,
                                                  horizontal_stride,
                                                  image_width):
            yield WindowCoordinates(h_window.start, v_window.start,
                                    h_window.end, v_window.end)


def export_image_cutouts(
        image_path: Path,
        output_dir: Path) -> Generator[WindowMetadata, None, None]:
    """Export cutouts of the provided image path to output directory.

    Parameters
    ----------
    image_path: Path, required
        The path of the image to export into cutouts.
    output_dir: Path, required
        The path of the output directory.

    Returns
    -------
    export_metadata: generator of WindowMetadata
        The metadata of each cutout.
    """
    image_file = str(image_path)
    logging.info("Segmenting image %s.", image_file)
    source_img = read_image_grayscale(image_file)
    img_width, img_height = get_cv2_image_size(source_img)
    export_name = f'{image_path.parts[-2]}-{image_path.stem}'

    coordinates = calculate_window_coordinates(
        img_width,
        img_height,
        args.window_size,
        horizontal_stride=args.horizontal_stride,
        vertical_stride=args.vertical_stride)

    for idx, w in enumerate(coordinates):
        file_name = f'{export_name}-w{idx:02d}.png'
        window = source_img[w.top_left_y:w.bottom_right_y,
                            w.top_left_x:w.bottom_right_x]
        cv.imwrite(str(output_dir / file_name), window)
        yield WindowMetadata(img_width, img_height, file_name,
                             args.window_size, w.top_left_x, w.top_left_y,
                             w.bottom_right_x, w.bottom_right_y)


def save_metadata(metadata: List[WindowMetadata], output_dir: Path,
                  output_file: str):
    """Save metadata to a CSV file.

    Parameters
    ----------
    metadata: list of WindowMetadata, required
        The metadata of the exported cutouts.
    output_dir: Path, required
        The path of the output directory.
    output_file: str, required
        The name of the CSV file within the output directory where to save metadata.
    """
    metadata_file = str(output_dir / output_file)
    logging.info("Saving segmented images metadata to %s.", metadata_file)
    df = pd.DataFrame(metadata,
                      columns=[
                          'image_width', 'image_height', 'window_name',
                          'window_size', 'top_left_x', 'top_left_y',
                          'bottom_right_x', 'bottom_right_y'
                      ])
    df.to_csv(metadata_file, index=False)


def main(args: Namespace):
    """Read images from input directory and export segmented images to output directory.

    Parameters
    ----------
    args: Namespace, required
        The command-line arguments.
    """
    msg = f'Segmenting images from {args.input_dir} with the following parameters: '
    msg += f'window size={args.window_size}, '
    msg += f'horizontal stride={args.horizontal_stride}, '
    msg += f' vertical stride={args.vertical_stride}.'
    logging.info(msg)

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        logging.info("Creating directory %s.", str(output_dir))
        output_dir.mkdir()

    metadata = []
    for image in Path(args.input_dir).glob('*.png'):
        for metadata_item in export_image_cutouts(image, output_dir):
            metadata.append(metadata_item)

    save_metadata(metadata, output_dir, args.metadata_file)
    logging.info("Done.")


def parse_arguments() -> Namespace:
    """Parse the command-line arguments.

    Returns
    -------
    args: Namespace
        The command-line arguments.
    """
    parser = ArgumentParser(description='Generate windows from images.')
    parser.add_argument('--input-dir',
                        help="The input directory.",
                        required=True)
    parser.add_argument(
        '--output-dir',
        help="The output directory. Default value is './segmented-images'.",
        default='./segmented-images')
    parser.add_argument('--window-size',
                        help="The size of the image windows.",
                        type=int,
                        default=320)

    parser.add_argument('--horizontal-stride',
                        help="The horizontal stride.",
                        type=int,
                        default=140)
    parser.add_argument('--vertical-stride',
                        help="The vertical stride.",
                        type=int,
                        default=160)
    parser.add_argument(
        '--metadata-file',
        help="The path of the CSV file containing window metadata.",
        type=str,
        default="metadata.csv")
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
    main(args)
