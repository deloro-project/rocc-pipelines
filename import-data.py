import logging
from argparse import ArgumentParser
from zipfile import ZipFile
import re


def import_data(input_file, include_files=None):
    """Reads the contents of the input archive and prepares the files for import.

    Parameters
    ----------
    input_file: str, required
        The full path to the zip archive containing files to import.
    include_files: str, optional
        A RegEx pattern that in matched against the full path of each
        file within archive. If a value is provided then only files with
        matching file names will be processed.
        Default is None which means process all files.
    """
    with ZipFile(input_file) as zip_archive:
        for f in zip_archive.namelist():
            if (not include_files) or (re.match(include_files, f)):
                print(f)


def parse_arguments():
    parser = ArgumentParser()

    parser.add_argument('--input-file',
                        help="Full path of the input archive (zip) file.")
    parser.add_argument('--include-files',
                        help="The regex pattern for files to include")
    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO)
    args = parse_arguments()
    import_data(**args.__dict__)
    logging.info("That's all folks!")
