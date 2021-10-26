"""Exports lexicons from line annotations and transcribed files."""
import argparse
import logging
import spacy
import re
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


def is_valid_token(token):
    """Check if token is valid.

    Parameters
    ----------
    token: str, required
        The token to process.

    Returns
    -------
    is_valid: bool
        True if token is valid; False otherwise.
    """
    # Remove spaces from token
    token = token.replace(' ', '')
    if len(token) == 0:
        return False
    if re.search(r'[0-9\.,?=:/"]', token):
        return False
    # Exclude tokens that start or end with dash '-'
    # This usually signals that a single word was split into two lines
    if (token[0] == '-' or token[-1] == '-'):
        return False
    # Exclude single-character tokens that contain various marks
    if len(token) == 1:
        return token in ['›', '‹', '"']

    return True


def build_vocabulary(documents):
    """Build vocabulary from provided documents.

    Parameters
    ----------
    documents: iterable of str, required
        The documents from which to build vocabulary.

    Returns
    -------
    vocabulary: set of str
        The set of vocabulary terms.
    """
    nlp = spacy.load('ro_core_news_lg')
    tokens = [
        str(token) for text in documents for token in nlp(text=text)
        if is_valid_token(str(token))
    ]
    return set([token.lower() for token in tokens])


def format_period(period):
    """Build a pretty name for a time interval.

    Parameters
    ----------
    period: pandas.Interval, required
        The time interval to format.

    Returns
    -------
    name: str
        The period name in format '<period.left>-<period.right>'.
    """
    left, right = int(period.left), int(period.right)
    return '{left}-{right}'.format(left=left, right=right)


def build_vocabulary_file_name(period):
    """Build vocabulary file name for given period.

    Parameters
    ----------
    period: pandas.Interval, required
        The time period for which to build file name.

    Returns
    -------
    file_name: str
        The file name in format '<period.left>-<period.right>.csv'.
    """
    return "{name}.csv".format(name=format_period(period))


def to_csv(dataframe, file_name, write_header):
    """Save provided dataframe to specified file name in CSV format.

    Parameters
    ----------
    dataframe: pandas.DataFrame, required
        The data frame to save.
    file_name: str, required
        The full name of the file where to save the dataframe.
    write_header: bool, required
        Specifies whether to write the header row or not.
    """
    dataframe.to_csv(file_name, index=False, header=write_header)


def save_data_frame(df, title, output_dir, file_name, write_header):
    """Save data frame to specified path.

    Parameters
    ----------
    df: pandas.DataFrame, required
        The data frame to save.
    title: str, required
        The title of data frame; this will be displayed in logging message.
    output_dir: str, required
        The parent directory of the file in which to save the data frame.
        If directory does not exist, it will be created.
    file_name: str, required
        The name of the file in which to save the data frame.
    write_header: bool, required
        Specifies whether to write header row of the data frame or not.
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    path = path / file_name
    file_name = str(path)
    logging.info("Saving {what} in {where}.".format(what=title,
                                                    where=file_name))
    to_csv(df, file_name, write_header)


def save_vocabulary(vocab, directory_name, file_name, write_header=False):
    """Save provided vocabulary in the specified file and directory.

    Parameters
    ----------
    vocab: iterable of str, required
        The iterable containing vocabulary terms.
    directory_name: str, required
        The directory where to save vocabulary.
    file_name: str, required
        The name of the file where to save vocabulary.
    write_heaeder: bool, optional
        Specifies whether the output file should contain a header row.
        Default is False.
    """
    path = Path(directory_name)
    path.mkdir(parents=True, exist_ok=True)
    path = path / file_name
    file_path = str(path)
    logging.info("Saving {count} tokens from lexicon into file {file}.".format(
        file=file_path, count=len(vocab)))
    df = pd.DataFrame(vocab, columns=['Term'])
    logging.info(df)
    to_csv(df, file_path, write_header)


def calculate_statistics(stats_table, vocab, period):
    """Calculate statistics for the provided vocabulary and add them to stats table.

    Parameters
    ----------
    stats_table: dict, required
        The dictionary containing statistics.
    vocab: iterable of str, required
        The vocabulary for which to compute statistics.
    period: pandas.Interval, required
        The period of the vocabulary.
    """
    if 'period' not in stats_table:
        stats_table['period'] = []
    if 'num_tokens' not in stats_table:
        stats_table['num_tokens'] = []
    stats_table['period'].append(format_period(period))
    stats_table['num_tokens'].append(len(vocab))


def trace_words_in_periods(vocabs):
    """Builds a table of common words accross periods.

    Parameters
    ----------
    vocabs: dict of <str, set>, required
        The vocabularies as a dictionary with key=period and value=vocabuldary.

    Returns
    -------
    term_appearances: pandas.DataFrame
        A dataframe containing a row for each term that appears in
        more than one period. For each available period, the row
        will contain True if the term appears in the lexicon of that
        periods and False otherwise.
    """
    # Build the structure of the output dictionary
    period_columns = sorted([period for period, _ in vocabs.items()])
    columns = ['term'] + period_columns
    data = {col: [] for col in columns}

    # Build a global vocabulary containing the union of all terms
    global_vocab = set()
    for _, vocab in vocabs.items():
        global_vocab = global_vocab.union(vocab)

    # Iterate the global vocabulary and find the periods in which
    # each term appears. If the term appears in two or more periods
    # then it is added to output dictionary.
    for term in global_vocab:
        periods = [period for period, lexic in vocabs.items() if term in lexic]
        if len(periods) > 1:
            logging.info(
                "Adding term '{}' to table of common terms.".format(term))
            data['term'].append(term)
            for col in period_columns:
                data[col].append(col in periods)

    term_appearances = pd.DataFrame(data)
    num_rows, _ = term_appearances.shape
    logging.info('Found {} common terms.'.format(num_rows))
    logging.info(term_appearances)
    return term_appearances


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

    bins = np.array([1500, 1550, 1600, 1650, 1700, 1750, 1800, 1850, 1900])
    data['period'] = pd.cut(data.publishing_year, bins)
    stats, vocabs = {}, {}
    for period in data.period.unique():
        if isinstance(period, float):
            continue

        logging.info("Building lexicon for period {}.".format(period))
        documents = [d for d in data[data.period == period].document]
        vocab = build_vocabulary(documents)
        file_name = build_vocabulary_file_name(period)
        save_vocabulary(vocab,
                        args.output_dir,
                        file_name,
                        write_header=args.write_header)
        calculate_statistics(stats, vocab, period)
        vocabs[format_period(period)] = vocab

    save_data_frame(pd.DataFrame(stats), 'lexicon size statistics',
                    args.output_dir, args.size_stats_file, True)

    save_data_frame(trace_words_in_periods(vocabs),
                    'lexicon terms per periods', args.output_dir,
                    args.terms_per_periods_file, True)

    logging.info("That's all folks!")


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
        '--write-header',
        help="Specifies whether to add header row to lexicon export files.",
        action='store_true')
    parser.add_argument(
        '--size-stats-file',
        help="The name of the file containing size statistics.",
        default="size-stats.csv")
    parser.add_argument(
        '--terms-per-periods-file',
        help="The name of the file tracing lexicon terms per periods.",
        default='lexicon-per-periods.csv')
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
