"""Exports letter annotations to CSV file."""
import logging
from pathlib import Path
import argparse
from exportutils import load_annotations
import numpy as np


def copy_images(image_paths, destination_dir, images_root):
    """Copy page images to the destination directory.

    Parameters
    ----------
    image_paths : iterable of str, required
        The collection of images to copy to the destination directory.
    destinaiton_dir: str, required
        The destination directory.
    images_root: str, required
        The root directory from which to start replicating the hierarchy.

    Returns:
    -------
    name_map: dict of (str, str)
        A dictionary containing the mapping between the original image file
        and the exported file.
    """
    name_map = {}
    images_root = Path(images_root)
    for img_path in image_paths:
        if str(img_path) in name_map:
            continue
        try:
            src_path = Path(img_path)
            dest_path = Path(destination_dir,
                             *src_path.parts[len(images_root.parts):])
            logging.info('Copying page image {src} to {dest}.'.format(
                src=str(src_path), dest=str(dest_path)))

            dest_dir = dest_path.parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(src_path.read_bytes())
            # Make sure that the destination path does not contain
            # output directory when adding it to the name map
            dest_path = Path(*dest_path.parts[1:])
            name_map[str(src_path)] = str(dest_path)
        except Exception as ex:
            logging.warning("Error trying to save image {}. {}".format(
                img_path, ex))
    return name_map


def run(args):
    """Export annotations to specified file."""
    letters_df, lines_df = load_annotations(args.db_server,
                                            args.db_name,
                                            args.user,
                                            args.password,
                                            port=args.port)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    letters_csv_path = Path(args.output_dir, args.letter_annotations_file)
    lines_csv_path = Path(args.output_dir, args.line_annotations_file)
    image_paths = np.union1d(letters_df.page_file_name.unique(),
                             lines_df.page_file_name.unique())
    name_map = copy_images(image_paths, args.output_dir, args.images_root)

    logging.info("Saving letter annotations to CSV file {}.".format(
        str(letters_csv_path)))
    letters_df.page_file_name = letters_df.page_file_name.map(name_map)
    letters_df.to_csv(str(letters_csv_path))

    logging.info("Saving line annotations to CSV file {}.".format(
        str(lines_csv_path)))
    lines_df.page_file_name = lines_df.page_file_name.map(name_map)
    lines_df.to_csv(str(lines_csv_path))


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Arguments for exporting annotations.')
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
        help="The path of the output directory. Default value is './export'.",
        default='./export')
    parser.add_argument(
        '--letter-annotations-file',
        help="Name of the CSV file containing the annotations.",
        default="letter-annotations.csv")
    parser.add_argument(
        '--line-annotations-file',
        help="Name of the CSV file containing the annotations.",
        default="line-annotations.csv")
    parser.add_argument('--images-root',
                        help="Images root directory.",
                        default='/mnt/deloro/')
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
    run(args)
    logging.info("That's all folks!")
