import logging
from argparse import ArgumentParser
from zipfile import ZipFile
import re
from pathlib import PurePath, Path
from pdf2image import convert_from_bytes
import unidecode


def build_output_file_name(file_name, remove_root_dir, output_root_dir):
    """Builds a normalized output file name.

    Parameters
    ----------
    file_name: str, required
        The initial file name.
    remove_root_dir: boolean, required
        Specifies whether to remove the root directory from the initial path.
    output_root_dir: str, required
        The root directory of the output file.

    Returns
    -------
    pathlib.Path
        The path of the output file.
    """
    path = PurePath(unidecode.unidecode(file_name))
    if remove_root_dir:
        path = PurePath(output_root_dir, *path.parts[1:])
    else:
        path = output_root_dir / path

    def normalize(path):
        path = re.sub(r'[^a-z/.0-9]+', '-', path, flags=re.IGNORECASE)
        return path.lower()

    path = Path(*[normalize(segment) for segment in path.parts])
    return path


def can_import(path):
    """Determines whether the specified path can be imported.

    Parameters
    ----------
    path: pathlib.Path, required
        The path to check.

    Returns
    -------
    (able_to_import, requires_splitting)
        able_to_import is True if the path can be imported; False otherwise.
        requires_splitting is True if the file is a PDF and needs to be split into images.
    """
    extension = path.suffix if path.suffix else ''
    extension = extension.lower()
    able_to_import = extension in ['.pdf', '.png', '.jpg', '.jpeg', '.xml']
    requires_splitting = extension == '.pdf'
    return able_to_import, requires_splitting


def expand_file_name(path, page_tag, page_number, image_format):
    """Expands the file name given by path into a file name for the specified page number and image format.

    Parameters
    ----------
    path: pathlib.Path, required
        The file path to expand.
    page_tag: str, required
        The token used to split file name from page number.
    page_number: int, required
        The page for which to expand the file name.
    image_format: str, required
        The extension of the expanded file name.

    Returns
    -------
    pathlib.Path
        The file name of the given page as an image.
    """
    output_path = PurePath(path.parent)
    file_name = "{}-{}-{}.{}".format(path.stem, page_tag, page_number,
                                     image_format)
    return Path(path.parent, file_name)


def import_data(input_file,
                include_files=None,
                remove_root_dir=True,
                output_dir='./data',
                pdf_split_dpi=600,
                pdf_split_format='png',
                pdf_split_page_tag='pagina'):
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
    remove_root_dir: boolean, optional
        Specifies whether to remove the root directory from the path of
        each file contained in the input archive. Default is True.
    output_dir: str, optional
        Specifies the root output directory. Default is './data'.
    pdf_split_dpi: integer, optional
        Specifies the DPI of the images generated from splitting pdf files. Default is 600.
    pdf_split_format: str, optional
        Specifies the output format of the images generated from splitting pdf files. Default is png.
    pdf_split_page_tag: stri, optional
        Specifies the token that joins the PDF file name and the page number. Default is 'pagina'.
    """
    logging.info("Reading contents of input file {}.".format(input_file))

    with ZipFile(input_file) as zip_archive:
        for f in zip_archive.namelist():
            if (not include_files) or (re.search(include_files, f,
                                                 re.IGNORECASE)):
                logging.info("Processing {}.".format(f))
                output_path = build_output_file_name(f, remove_root_dir,
                                                     output_dir)
                is_importable, requires_splitting = can_import(output_path)
                if not is_importable:
                    logging.info(
                        "[{}] cannot be imported. Skipping.".format(f))
                    continue

                parent_dir = Path(output_path.parent)
                logging.info("Creating directory [{}]".format(parent_dir))
                parent_dir.mkdir(parents=True, exist_ok=True)

                payload = zip_archive.read(f)
                if requires_splitting:
                    logging.info("Splitting file [{}] into images.".format(f))
                    images = convert_from_bytes(payload,
                                                dpi=pdf_split_dpi,
                                                fmt=pdf_split_format)
                    logging.info("File [{}] was split into {} images.".format(
                        f, len(images)))
                    for i, page in enumerate(images):
                        image_path = expand_file_name(output_path,
                                                      pdf_split_page_tag, i,
                                                      pdf_split_format)
                        logging.info("Saving file [{}].".format(image_path))
                        page.save(image_path)
                else:
                    logging.info("Extracting to [{}].".format(output_path))
                    output_path.write_bytes(payload)


def parse_arguments():
    parser = ArgumentParser()

    parser.add_argument('--input-file',
                        help="Full path of the input archive (zip) file.")
    parser.add_argument('--include-files',
                        help="The regex pattern for files to include")
    parser.add_argument(
        '--remove-root-dir',
        help=
        "Specifies whether to remove the root directory of the files from the input.",
        action='store_true')
    parser.add_argument(
        '--output-dir',
        help="The root directory where to extract the contents of the archive.",
        default="./data")
    parser.add_argument(
        '--pdf-split-dpi',
        help=
        "The DPI of the images generated from splitting pdf files. Default is 600.",
        type=int,
        default=600)
    parser.add_argument(
        '--pdf-split-format',
        help=
        "The output format of the images generated from splitting pdf files. Default is png.",
        default='png')
    parser.add_argument(
        '--pdf-split-page-tag',
        help=
        "Specifies the token that joins the PDF file name and the page number. Default is 'pagina'.",
        default='pagina')
    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO)
    args = parse_arguments()
    import_data(**args.__dict__)
    logging.info("That's all folks!")
