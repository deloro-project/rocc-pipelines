import logging
from argparse import ArgumentParser


def run(input_file):
    pass


def parse_arguments():
    parser = ArgumentParser()

    parser.add_argument('--input-file',
                        help="Full path of the input archive (zip) file.")
    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO)
    args = parse_arguments()
    run(**args.__dict__)
    logging.info("That's all folks!")
