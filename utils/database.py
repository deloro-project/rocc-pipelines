#!/usr/bin/env python
"""Utility functions for loading data from database."""
import logging
from sqlalchemy import create_engine
import pandas as pd
from sklearn.model_selection import train_test_split

DEBUG_MODE = False
NUM_DEBUG_SAMPLES = 100
RANDOM_SEED = 2022


def load_annotations(server, database, user, password, port=5432):
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
    (letters_df, lines_df) : tuple of pandas.DataFrame
        Dataframes containing all the annotations.
    """
    logging.info("Loading annotations from database...")
    template = 'postgresql://{user}:{password}@{server}:{port}/{database}'
    conn_str = template.format(user=user,
                               password=password,
                               server=server,
                               port=port,
                               database=database)

    engine = create_engine(conn_str)
    with engine.connect() as conn:
        letters_df = pd.read_sql('select * from letter_annotations', conn)
        lines_df = pd.read_sql('select * from line_annotations', conn)

    num_rows, _ = letters_df.shape
    logging.info(
        "Finished loading {} letter annotations from database.".format(
            num_rows))
    num_rows, _ = lines_df.shape
    logging.info("Finished loading {} lines annotations from database.".format(
        num_rows))
    return letters_df, lines_df


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

    Returns
    -------
    letters_df: pandas.DataFrame
        The dataframe containing letter annotations.
    """
    user, password = credentials
    letters_df, _ = load_annotations(db_server, db_name, user, password, port)
    letters_df = letters_df[[
        'page_file_name', 'letter', 'left_up_horiz', 'left_up_vert',
        'right_down_horiz', 'right_down_vert'
    ]]

    if DEBUG_MODE:
        logging.info(
            "Running in debug mode; database results are truncated to {} rows."
            .format(NUM_DEBUG_SAMPLES))
        letters_df = letters_df.head(NUM_DEBUG_SAMPLES)

    if top_labels:
        return filter_letter_annotations(letters_df, top_labels)

    return letters_df
