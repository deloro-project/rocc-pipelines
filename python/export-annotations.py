"""Exports letter annotations to CSV file."""
import logging
from pathlib import Path
import argparse
from sqlalchemy import create_engine
import pandas as pd


def load_data(server, database, user, password, port=5432):
    """Load the annotations from a PostgreSQL database into a padans DataFrame.

    Parameters
    ----------
    server : str, required
        The name or IP address of the database server.
    database : str, required
        The name of the database containing annotations.
    user : str, required
        The username which is allowed to connect to the database.
    password : str, required
        The password of the username.
    port : str, optional
        The port for connecting to the database.

    Returns
    -------
    df : pandas.DataFrame
        A dataframe containing all the annotations.
    """
    logging.info("Loading annotations from database...")
    conn_str = 'postgresql://{user}:{password}@{server}:{port}/{database}'.format(
        user=user,
        password=password,
        server=server,
        port=port,
        database=database)
    engine = create_engine(conn_str)
    with engine.connect() as conn:
        df = pd.read_sql('select * from letter_annotations', conn)

    num_rows, _ = df.shape
    logging.info(
        "Finished loading {} annotations from database.".format(num_rows))
    return df


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
            dest_path = Path(destination_dir, *src_path.parts[len(images_root.parts):])
            logging.info('Copying page image {src} to {dest}.'.format(
                src=str(src_path), dest=str(dest_path)))

            dest_dir = dest_path.parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(src_path.read_bytes())
            # Make sure that the destination path does not contain output directory
            # when adding it to the name map
            dest_path = Path(*dest_path.parts[1:])
            name_map[str(src_path)] = str(dest_path)
        except Exception as ex:
            logging.warning("Error trying to save image {}. {}".format(
                img_path, ex))
    return name_map


def run(args):
    df = load_data(args.db_server,
                   args.db_name,
                   args.user,
                   args.password,
                   port=args.port)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    csv_path = Path(args.output_dir, args.annotations_file)
    name_map = copy_images(df.page_file_name.unique(), args.output_dir,
                           args.images_root)
    logging.info("Saving annotations to CSV file {}.".format(str(csv_path)))
    df.page_file_name = df.page_file_name.map(name_map)
    df.to_csv(str(csv_path))


def parse_arguments():
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
        '--annotations-file',
        help="Name of the CSV file containing the annotations.",
        default="letter_annotations.csv")
    parser.add_argument(
        '--images-root',
        help=
        "The directory below which to replicate the directory structure in exported images.",
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
