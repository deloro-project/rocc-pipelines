import logging
from argparse import ArgumentParser
from zipfile import ZipFile
from pathlib import PurePath, Path
import argparse


def run(args):
    pass


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Arguments for exporting annotations.')
    parser.add_argument('--output-dir',
                        help="The path of the output directory. Default value is './output'.",
                        default='./output')
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
