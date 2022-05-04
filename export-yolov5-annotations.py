#!/usr/bin/env python
"""Exports letter and line annotations into Yolo v5 format."""
import argparse
import logging
from exportutils import load_annotations
from exportutils import create_directories
from io import StringIO
from pathlib import Path

def save_dataset_description(train, val, labels, yaml_file):
    # Hack: PyYaml does not quote the label names; as such
    # we have to print the labels and pass the resulting string
    with StringIO() as output:
        print(labels, file=output)
        names = output.getvalue()

    yaml_content = """# Data directories
train: {train}
val: {val}

# Number of classes
nc: {nc}

# Label names
names: {names}
"""

    with open(yaml_file, 'w') as f:
        f.write(
            yaml_content.format(train=train,
                                val=val,
                                nc=len(labels),
                                names=names))


def main(args):
    """Export annotations in Yolo v5 format.

    Parameters
    ----------
    args: argparse.Namespace, required
        The arguments of the script.
    """
    letters_df, lines_df = load_annotations(args.db_server,
                                            args.db_name,
                                            args.user,
                                            args.password,
                                            port=args.port)
    labels = list(letters_df.letter.unique())
    # for each label in dataframe:
    # - train, test = train_test_split
    # - for each row in train/test:
    #   - get image name
    #   - copy image
    #   - resize image
    #   - build bounding box based on original image size
    #   - reshape bounding box based on new image size
    #   - append to the labels file
    export_dir = Path(args.output_dir) / 'letters'
    train_dir = export_dir / 'train'
    val_dir = export_dir / 'val'
    yaml_file = export_dir / 'letters.yaml'
    create_directories(train_dir, val_dir, yaml_file)
    save_dataset_description(str(train_dir), str(val_dir), labels, str(yaml_file))

    letters_df.to_csv(str(export_dir / 'letters.csv'))


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Export annotations for Yolo v5.')
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
        help="The path of the output directory. Default value is './yolo-export'.",
        default='./yolo-export')

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
    logging.info("That's all folks!")
