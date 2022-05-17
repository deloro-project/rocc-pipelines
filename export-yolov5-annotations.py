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

RANDOM_SEED = 2022
TEST_SIZE = 0.2


def filter_letter_annotations(letters_df, top_size):
    """Filter letter annotations by top number of samples.

    Parameters
    ----------
    letters_df: pandas.DataFrame, required
        The dataframe containing letter annotations.
    top_size: float, required
        The percent of top labels to return sorted by size.

    Returns
    -------
    letters_df: pandas.DataFrame
        The filtered dataframe.
    """
    logging.info("Filtering letter annotations to top {} percent.".format(
        top_size * 100))
    labels = list(letters_df.letter.unique())
    _, x = train_test_split(labels,
                            test_size=top_size,
                            random_state=RANDOM_SEED)
    letter_groups = letters_df.groupby(
        letters_df.letter)['letter'].count().nlargest(len(x))
    letter_groups = list(letter_groups.index)
    logging.info("Only the following labels will be exported: {}.".format(
        ', '.join(letter_groups)))
    return letters_df[letters_df.letter.map(lambda l: l in letter_groups)]


def load_letter_annotations(db_server,
                            db_name,
                            credentials,
                            port,
                            top_labels=None):
    """Load letter annotations from database and optionally filters the ones with higher number of samples.

    Parameters
    ----------
    db_server: str, required
        The database server.
    db_name: str, required
        The database name.
    credentials: tuple of (str, str), required
        The user name and password for connecting to the database.
    port: int, required
        The port for database server.
    top_labels: float between 0 and 1, optional
        The top percent of labels to return when ordered descendingly by number of samples.
        Default is None; when 0 or None returns all labels.
    """
    user, password = credentials
    letters_df, _ = load_annotations(db_server, db_name, user, password, port)
    letters_df = letters_df[[
        'page_file_name', 'letter', 'left_up_horiz', 'left_up_vert',
        'right_down_horiz', 'right_down_vert'
    ]]

    if top_labels:
        return filter_letter_annotations(letters_df, top_labels)

    return letters_df


def save_dataset_description(train, val, labels, yaml_file):
    """Save dataset description to YAML file.

    Parameters
    ----------
    train: str, required
        The path to the training directory.
    val: str, required
        The path to the validation directory.
    labels: list of str, required
        The list of class labels.
    yaml_file: str, required
        The path of the output YAML file.
    """
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


def get_export_file_names(image_path):
    """Get the names of the export files from original image path.

    Parameters
    ----------
    image_path: str, required
        The path of the original image.

    Returns
    -------
    (image_name, labels_name): tuple of (str, str
        The name of the image to export.
    """
    path = Path(image_path)
    image_name = '{parent}-{image}.png'.format(parent=path.parts[-2],
                                               image=path.stem)
    labels_name = '{parent}-{image}.txt'.format(parent=path.parts[-2],
                                                image=path.stem)
    return image_name, labels_name


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
    logging.info("Exporting image {} to {}.".format(src_path, dest_path))
    with Image.open(src_path) as source:
        destination = source.resize((width, height))
        destination.save(dest_path)
        destination.close()


def scale_coordinates(top_left, bottom_right, original_size, export_size):
    """Scale provided coordinates to the size of exported image.

    Parameters
    ----------
    top_left: tuple of (number, number), required
        The (x, y) coordinates of the top-left point.
    bottom_right: tuple of (number, number), required
        The (x, y) coordinates of the bottom-right point.
    original_size: tuple of (int, int), required
        The size in pixels (w, h) of the original image.
    export_size: tuple of (int, int), required
        The size in pixels (w, h) of the exported (resized) image.

    Returns
    -------
    scaled_coordinates: tuple of ((number, number), (number, number))
        The (top-left, bottom-right) coordinates scaled from original size to the export size.
    """
    original_width, original_height = original_size
    width, height = export_size
    horiz_scale = width / original_width
    vert_scale = height / original_height
    x1, y1 = top_left
    x2, y2 = bottom_right

    return (round(x1 * horiz_scale),
            round(y1 * vert_scale)), (round(x2 * horiz_scale),
                                      round(y2 * vert_scale))


def calculate_bounding_box(top_left, bottom_right, image_size):
    """Calculate the center point and dimensions of the bounding box.

    Parameters
    ----------
    top_left: tuple of (number, number), required
        The (x, y) coordinates of the top-left point.
    bottom_right: tuple of (number, number), required
        The (x, y) coordinates of the bottom-right point.
    image_size: tuple of (number, number), required
        The size of the image (width, height).

    Returns
    -------
    (center, dimensions): tuple of (center point coordinates, dimensions of the rectangle)
        The coordinates of center point (x, y), and dimensions (width, height) of the bounding box.
    """
    x1, y1 = top_left
    x2, y2 = bottom_right
    width, height = image_size

    x_center = round((x2 - x1) / 2)
    y_center = round((y2 - y1) / 2)
    x_center = x_center / width
    y_center = y_center / height

    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height

    return (x_center, y_center), (box_width, box_height)


def export_bounding_boxes(left_up_horiz, left_up_vert, right_down_horiz,
                          right_down_vert, original_image_size,
                          export_image_size, labels_file, label_index):
    """Export bounding boxes to the labels file.

    Parameters
    ----------
    left_up_horiz: number, required
        Coordinate of the top-left point on the X scale.
    left_up_vert: number, required
        Coordinate of the top-left point in the Y scale.
    right_down_horiz: number, required
        Coordinate of the bottom-right point on the X scale.
    right_down_vert: number, required
        Coordinate of the bottom-right point in the Y scale.
    original_image_size: tuple of (int, int), required
        The size in pixels (w, h) of the original image.
    export_image_size: tule of (int, int), required
        The size in pixels (w, h) of the exported (resized) image.
    labels_file: str, required
        The path of the file containing labels.
    label_index: int, required
        The label index.
    """
    top_left, bottom_right = scale_coordinates(
        (left_up_horiz, left_up_vert), (right_down_horiz, right_down_vert),
        original_image_size, export_image_size)
    center, dimmensions = calculate_bounding_box(top_left, bottom_right,
                                                 export_image_size)
    x_center, y_center = center
    width, height = dimmensions
    with open(labels_file, 'a') as f:
        f.write("{label} {x} {y} {w} {h}".format(label=label_index,
                                                 x=x_center,
                                                 y=y_center,
                                                 w=width,
                                                 h=height))
        f.write("\n")


def export_collection(annotations, destination_directory, original_size_dict,
                      image_size, labels_map):
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
    labels_map: dict of (str, int), required
        The dictionary  that maps between a label and its index.
    """
    image_width, image_height = image_size
    for file_name, letter, *coords in annotations:
        image_name, labels_name = get_export_file_names(file_name)
        if image_name not in original_size_dict:
            try:
                export_image(file_name,
                             str(destination_directory / image_name),
                             image_width, image_height)
                with Image.open(file_name) as img:
                    original_size_dict[image_name] = img.size
            except (FileNotFoundError, IsADirectoryError):
                logging.error("Could not export image {}.".format(file_name))
                continue
        if letter not in labels_map:
            labels_map[letter] = len(labels_map)
        label_index = labels_map[letter]
        export_bounding_boxes(*coords, original_size_dict[image_name],
                              image_size,
                              str(destination_directory / labels_name),
                              label_index)


def main(args):
    """Export annotations in Yolo v5 format.

    Parameters
    ----------
    args: argparse.Namespace, required
        The arguments of the script.
    """
    letters_df = load_letter_annotations(args.db_server, args.db_name,
                                         (args.user, args.password), args.port,
                                         args.top_labels)
    logging.info("Creating export directories for letter annotations.")
    train_dir, val_dir, yaml_file = create_export_directories(
        args.output_dir, export_type='letters')

    letter_groups = letters_df.groupby(letters_df.letter)
    image_size_dict = {}
    labels_map = {}
    for letter, group in letter_groups:
        logging.info("Exporting data for label {}.".format(letter))
        ds = group.to_numpy()
        num_samples, _ = ds.shape
        if num_samples < 2:
            logging.warning(
                "There are not enough samples to split for label {}.".format(
                    letter))
            continue

        train, val = train_test_split(ds,
                                      test_size=TEST_SIZE,
                                      random_state=RANDOM_SEED)
        logging.info("Exporting training data.")
        export_collection(train, train_dir, image_size_dict, args.image_size,
                          labels_map)
        logging.info("Exporting validation data.")
        export_collection(val, val_dir, image_size_dict, args.image_size,
                          labels_map)
    labels = sorted(labels_map, key=labels_map.get)
    logging.info(
        "Saving letters dataset description file to {}.".format(yaml_file))
    save_dataset_description(str(train_dir), str(val_dir), labels,
                             str(yaml_file))


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

    parser.add_argument('--top-labels',
                        help="Percentage of top labels to export.",
                        type=float,
                        default=0.1)
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
