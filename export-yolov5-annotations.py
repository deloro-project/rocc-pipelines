#!/usr/bin/env python
"""Exports letter and line annotations into Yolo v5 format."""
import argparse
import logging
from exportutils import load_annotations
from exportutils import create_directories
from io import StringIO
from pathlib import Path
from sklearn.model_selection import train_test_split
from PIL import Image


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


def create_export_directories(output_directory, export_type='letters'):
    """Create directory structure for export.

    Parameters
    ----------
    output_directory: str, required
        The root directory where export data will reside.
    export_type: str, optional
        The type of export; can be either 'letters' or 'lines'.
        Default is 'letters'.

    Returns
    -------
    (train_dir, val_dir, yaml_file): tuple of pathlib.Path
        The directories for training data, validation data,
        and path of the dataset description file respectively.
    """
    export_type = 'lines' if export_type.lower() == 'lines' else 'letters'
    export_dir = Path(args.output_dir) / export_type
    train_dir = export_dir / 'train'
    val_dir = export_dir / 'val'
    yaml_file = export_dir / '{}.yaml'.format(export_type)
    create_directories(train_dir, val_dir)
    return train_dir, val_dir, yaml_file


def get_export_image_name(image_path):
    """Get the name of the exported image from original image path.

    Parameters
    ----------
    image_path: str, required
        The path of the original image.

    Returns
    -------
    image_name: str
        The name of the image to export.
    """
    path = Path(image_path)
    return '{parent}-{image}.png'.format(parent=path.parts[-2],
                                         image=path.stem)


def export_image(src_path, dest_path, width, height):
    """Export and resize the image.

    Parameters
    ----------
    src_path: str, required
        The source path of the image.
    dest_path: str, required
        The destination path of the image.
    width: int, required
        Width of the exported image.
    height: int, required
        Height of the exported image.
    """
    with Image.open(src_path) as source:
        destination = source.resize((width, height))
        destination.save(dest_path)
        destination.close()


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
    letters_df = letters_df[[
        'page_file_name', 'letter', 'left_up_horiz', 'left_up_vert',
        'right_down_horiz', 'right_down_vert'
    ]]

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
    logging.info("Creating export directories for letter annotations.")
    train_dir, val_dir, yaml_file = create_export_directories(
        args.output_dir, export_type='letters')
    logging.info(
        "Saving letters dataset description file to {}.".format(yaml_file))
    save_dataset_description(str(train_dir), str(val_dir), labels,
                             str(yaml_file))

    letter_groups = letters_df.groupby(letters_df.letter)
    image_size_dict = {}
    for letter, group in letter_groups:
        logging.info("Exporting data for label {}.".format(letter))
        ds = group.to_numpy()
        num_samples, _ = ds.shape
        if num_samples < 2:
            logging.info(
                "There are not enough samples to split for label {}.".format(
                    letter))
            continue

        train, val = train_test_split(ds, test_size=0.2, random_state=2022)
        logging.info("Exporting training data.")
        export_collection(train, train_dir, image_size_dict, args.image_size)
        logging.info("Exporting validation data.")
        export_collection(val, val_dir, image_size_dict, args.image_size)


def export_collection(annotations, destination_directory, original_size_dict,
                      image_size):
    """Export collection of annotations to destination directory.

    Parameters
    ----------
    annotations: iterable of tuples, required
        The collection of annotations to export.
    destination_directory: pathlib.Path, required
        The destination directory.
    original_size_dict: dict of (str, (int, int)), required
        The dict mapping exported image names to their original size.
    image_size: tuple of (int, int), required
        The size of exported images.
    """
    image_width, image_height = image_size
    for file_name, letter, *coords in annotations:
        export_file_name = get_export_image_name(file_name)
        if export_file_name not in original_size_dict:
            logging.info("Exporting image {} to {}.".format(
                file_name, export_file_name))
            export_image(file_name,
                         str(destination_directory / export_file_name),
                         image_width, image_height)
            with Image.open(file_name) as img:
                original_size_dict[export_file_name] = img.size


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
        help="The output directory. Default value is './yolo-export'.",
        default='./yolo-export')
    parser.add_argument(
        '--image-size',
        help="The size of the exported images. Default is [1024, 768].",
        type=int,
        nargs=2,
        default=[1024, 786])
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
