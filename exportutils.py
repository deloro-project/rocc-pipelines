#!/usr/bin/env python
"""Utility functions for annotations export."""
import logging
from sqlalchemy import create_engine
import pandas as pd


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
