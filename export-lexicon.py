"""Exports lexicons from line annotations and transcribed files."""
import argparse
import logging
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from pathlib import Path


def load_data(sql, server, database, user, password, port=5432):
    """Load data from database by running the provided sql query.

    Parameters
    ----------
    sql: str, required
        The SQL query to execute for loading data.
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
    data : padas.DataFrame
        A dataframe containing the data fetched from database.
    """
    conn_str = 'postgresql://{user}:{password}@{server}:{port}/{database}'
    conn_str = conn_str.format(user=user,
                               password=password,
                               server=server,
                               port=port,
                               database=database)
    engine = create_engine(conn_str)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


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

    sql = """
    SELECT PUB.PUBLISHINGYEAR AS PUBLISHING_YEAR, LA.LINE AS DOCUMENT
    FROM LINE_ANNOTATIONS LA
    JOIN PAGECOLLECTIONMETADATA PCM ON LA.PAGE_COLLECTION_ID = PCM.PAGECOLLECTIONID
    JOIN PUBLISHING PUB ON PCM.ROCCID = PUB.METADATAID
    """
    line_annotations = load_data(sql, server, database, user, password)
    num_rows, _ = line_annotations.shape
    logging.info("Finished loading {} lines annotations from database.".format(
        num_rows))
    return line_annotations


def load_transcribed_text_files(server, database, user, password, port=5432):
    """Load transcribed text files from disk.

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
    transcribed_texts : padas.DataFrame
        A dataframe containing transcribed texts with the following columns:
        - publishing_year
        - document
    """
    logging.info("Loading document metadata from database...")
    sql = """
    SELECT PUB.PUBLISHINGYEAR AS PUBLISHING_YEAR,
        PC.INTEGRALTRANSCRIBEDTEXTFILE AS DOCUMENT
    FROM PAGECOLLECTIONS PC
    JOIN PAGECOLLECTIONMETADATA PCM ON PC.ID = PCM.PAGECOLLECTIONID
    JOIN PUBLISHING PUB ON PCM.ROCCID = PUB.METADATAID
    """
    data = load_data(sql, server, database, user, password)
    num_rows, _ = data.shape
    logging.info(
        "Finished loading {} metadata rows from database.".format(num_rows))
    documents = {'publishing_year': [], 'document': []}
    for row in data.itertuples():
        file_path = Path(row.document)
        if file_path.suffix == '.xml':
            logging.info("Ignoring XML document {}.".format(row.document))
            continue
        if not file_path.exists():
            logging.warning("File {} does not exist.".format(row.document))
            continue
        if not file_path.is_file():
            logging.warning("Path {} does not point to a file.".format(
                row.document))
            continue
        logging.info('Adding document {} to documents dataframe.'.format(
            row.document))
        documents['publishing_year'].append(row.publishing_year)
        documents['document'].append(file_path.read_text(encoding='utf8'))

    return pd.DataFrame(documents)


def run(args):
    """Run the export."""
    lines_df = load_line_annotations(args.db_server, args.db_name, args.user,
                                     args.password)
    documents_df = load_transcribed_text_files(args.db_server, args.db_name,
                                               args.user, args.password)
    logging.info(
        "Combining line annotations and transcribed files into single dataset")
    data = lines_df.append(documents_df)
    if data.shape[0] != lines_df.shape[0] + documents_df.shape[0]:
        logging.error("Data lost when combining documents.")


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

# TODO: Group texts into sliding windows of 50 years periods
# TODO: Build lexicon for each time period
# TODO: Save lexicon to output directory
