"""Exports lexicons from line annotations and transcribed files."""
import argparse
import logging
import pandas as pd
from sqlalchemy import create_engine


def load_line_annotations(server, database, user, password, port=5432):
    """Load line annotations from the database specified by parameters.

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
    line_annotations : padas.DataFrame
        A dataframe containing line annotations with the following columns:
        - publishing_year
        - document
    """
    logging.info("Loading annotations from database...")
    conn_str = 'postgresql://{user}:{password}@{server}:{port}/{database}'
    conn_str = conn_str.format(user=user,
                               password=password,
                               server=server,
                               port=port,
                               database=database)
    sql = """
    SELECT PUB.PUBLISHINGYEAR AS PUBLISHING_YEAR, LA.LINE AS DOCUMENT
    FROM LINE_ANNOTATIONS LA
    JOIN PAGECOLLECTIONMETADATA PCM ON LA.PAGE_COLLECTION_ID = PCM.PAGECOLLECTIONID
    JOIN PUBLISHING PUB ON PCM.ROCCID = PUB.METADATAID
    """
    engine = create_engine(conn_str)
    with engine.connect() as conn:
        line_annotations = pd.read_sql(sql, conn)

    num_rows, _ = line_annotations.shape
    logging.info("Finished loading {} lines annotations from database.".format(
        num_rows))
    return line_annotations


def run(args):
    """Run the export."""
    pass


def parse_arguments():
    """Parse command-lne arguments."""
    parser = argparse.ArgumentParser(description='Export lexicon')
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
        default='./lexii')
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

# TODO: Load transcribed text files
# TODO: Combine texts
# TODO: Group texts into sliding windows of 50 years periods
# TODO: Build lexicon for each time period
# TODO: Save lexicon to output directory
