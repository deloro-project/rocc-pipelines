#!/usr/bin/env python
"""Utility functions for file system."""
import logging
from pathlib import Path


def create_directories(*paths):
    """Create directory structure for the specified path.

    Parameters
    ----------
    paths: tuple of pathlib.Path, required
        The paths for which to create directories.
    """
    for path in paths:
        if path.exists():
            logging.info("Path {} already exists.".format(str(path)))
            continue

        logging.info("Creating directory {}.".format(str(path)))
        path.mkdir(parents=True, exist_ok=True)


def create_export_structure(output_directory, export_type):
    """Create directory structure for export.

    Parameters
    ----------
    output_directory: str, required
        The root directory where export data will reside.
    export_type: str, required
        The type of export; can be either 'letters', 'characters', or 'lines'.
        Default is 'letters'.

    Returns
    -------
    (staging_dir, train_dir, val_dir, yaml_file): tuple of pathlib.Path
        The directories for training data, validation data,
        and path of the dataset description file respectively.
    """
    export_dir = Path(output_directory) / export_type
    staging_dir = export_dir / 'staging_dir'
    train_dir = export_dir / 'train'
    val_dir = export_dir / 'val'
    yaml_file = export_dir / '{}.yaml'.format(export_type)
    create_directories(staging_dir, train_dir, val_dir)
    return staging_dir, train_dir, val_dir, yaml_file
