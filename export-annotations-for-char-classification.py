#!/usr/bin/env python
"""Exports character annotations on full images into Yolo v5 format."""
import argparse
import logging
import utils.database as db


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
        - output_dir: str - the root directory of the export.
    """
    logging.info("That's all folks!")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Export annotations on full images for Yolo v5.')
    parser.set_defaults(func=export_char_annotations)

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
