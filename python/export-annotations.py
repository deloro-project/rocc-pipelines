import logging
from argparse import ArgumentParser
from zipfile import ZipFile
from pathlib import PurePath, Path
import argparse
from sqlalchemy import create_engine, text
import pandas as pd


def load_data(server, database, user, password, port=5432):
    """Loads the annotations from a PostgreSQL database into a padans DataFrame.

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


def run(args):
    df = load_data(args.db_server,
                   args.db_name,
                   args.user,
                   args.password,
                   port=args.port)
    print(df)
    print(df.columns)


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
