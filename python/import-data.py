import logging
from argparse import ArgumentParser
from zipfile import ZipFile
import re
from pathlib import PurePath, Path
import unidecode
import tempfile
import fitz
from PIL import Image


class Constants:
    """Contains constants for the import script.
    """
    IMAGE_FORMAT = 'png'
    IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg']
    IMPORT_EXTENSIONS = ['.pdf', '.xml'] + ['.png', '.jpg', '.jpeg']
    CONVERT_EXTENSIONS = ['.jpg', '.jpeg']


class NormalizeRegex:
    """Contains the RegEx patterns as constants for normalizing file and directory names, and the replacement character.
    """
    FILE_NAME = re.compile(r'[^a-z\/.0-9]+', flags=re.IGNORECASE)
    DIRECTORY_NAME = re.compile(r'[^a-z\/0-9]+', flags=re.IGNORECASE)
    REPLACEMENT = '-'
    PAGE_NUMBER = re.compile(r'(?P<page>\d+)(?:(r|v)?\.)', re.MULTILINE)


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

    def normalize(path, pattern):
        path = pattern.sub(NormalizeRegex.REPLACEMENT, path)
        return path.lower()

    path = Path(normalize(str(path.parent), NormalizeRegex.DIRECTORY_NAME),
                normalize(path.parts[-1], NormalizeRegex.FILE_NAME))
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
    able_to_import = extension in Constants.IMPORT_EXTENSIONS
    requires_splitting = extension == '.pdf'
    return able_to_import, requires_splitting


def expand_file_name(path, page_tag, page_number, image_format, num_pages):
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
    num_pages: int, required
        The total number of pages in the document. Used to determine the number of left-padding zeroes in the page number.

    Returns
    -------
    pathlib.Path
        The file name of the given page as an image.
    """
    output_path = PurePath(path.parent)
    file_name = "{name}-{tag}-{page:0{padding}d}.{extension}".format(
        name=path.stem,
        tag=page_tag,
        page=page_number,
        extension=image_format,
        padding=len(str(num_pages)))
    return Path(path.parent, file_name)


def split_pdf_file(file_name, payload, output_path, page_tag):
    """Splits PDF file into images.

    Parameters
    ----------
    file_name: str, required
        The full path of the PDF file.
    payload: iterable of bytes
        The contents of the PDF file.
    output_path: str, required
        The full path of the PDF file if it were to be moved to the destination directory as is.
        From this parameter the file names of the resulting images will be built.
    page_tag: str, required
        The token that joins the PDF file name and the page number.
    """
    logging.info("Splitting file [{}] into images.".format(file_name))
    doc = fitz.open(stream=payload, filetype='pdf')
    logging.info("File [{}] has {} pages.".format(file_name, doc.pageCount))
    for page_number in range(doc.pageCount):
        image_path = expand_file_name(output_path, page_tag, page_number + 1,
                                      Constants.IMAGE_FORMAT, doc.pageCount)
        pix = doc[page_number].getPixmap(
            matrix=fitz.Matrix(100 / 72, 100 / 72))
        logging.info("Saving file [{}].".format(image_path))
        pix.writeImage(str(image_path), Constants.IMAGE_FORMAT)


def enforce_page_order(directory):
    """Renames images into the specified directory to ensure page order is preserved.

    Parameters
    ----------
    directory: str, required
        The path of the directory where to rename files.
    """
    pattern = r"(?P<page>\d+)(?:\.)"

    logging.info("Enforcing page order in directory [{}]".format(directory))
    path = Path(directory)
    # Assuming a single image type in each directory
    pages = [
        f for f in path.iterdir() if f.suffix in Constants.IMAGE_EXTENSIONS
    ]

    num_pages = len(pages)
    logging.info("Found {} pages in directory [{}]".format(
        num_pages, directory))
    padding = len(str(num_pages))
    for page in pages:
        page_number = NormalizeRegex.PAGE_NUMBER.search(str(page))
        if (not page_number) or (not page_number.group('page')):
            message = "Could not determine page number for [{}.]"
            logging.warning(message.format(str(page)))
            continue
        page_number = int(page_number.group('page'))
        name = re.sub(
            pattern,
            "{page_number:0{padding}d}.".format(page_number=page_number,
                                                padding=padding), str(page),
            re.MULTILINE)
        logging.info("Renaming file [{}] to [{}]".format(str(page), name))
        page.rename(name)


def convert_images_to_png(directory):
    """Converts the images from the specified directory into PNG format.

    Parameters
    ----------
    directory: str, required
        The path of the directory where to convert images.
    """
    logging.info(
        "Converting images to PNG format in directory {}.".format(directory))
    path = Path(directory)
    images = [
        img for img in path.iterdir()
        if img.suffix in Constants.CONVERT_EXTENSIONS
    ]

    num_images = len(images)
    if num_images == 0:
        logging.info("No images found for conversion in directory {}.".format(
            directory))
        return

    logging.info("Found {} images to convert in directory {}.".format(
        num_images, directory))
    for image in images:
        logging.info("Converting image [{}] to PNG format.".format(image))
        name = Path(directory, "{}.{}".format(image.stem,
                                              Constants.IMAGE_FORMAT))
        img = Image.open(str(image))
        img.save(str(name))
        image.unlink()


def process_archive_content_file(zip_archive, file_name, remove_root_dir,
                                 output_dir, pdf_split_page_tag,
                                 post_process_dirs):
    """Processes a file from the archive.

    Parameters
    ----------
    zip_archive: ZipFile, required
        The zip archive containing the file to process.
    file_name: str, required
        The file to process.
    remove_root_dir: boolean, required
        Specifies whether to remove the root directory from the path of the file.
    output_dir: str, required
        Specifies the root output directory.
    pdf_split_page_tag: str, required
        Specifies the token that joins the PDF file name and the page number.
    post_process_dirs: set of str
        The set where to add each directory that should be scheduled for post processing.
    """
    logging.info("Processing {}.".format(file_name))
    output_path = build_output_file_name(file_name, remove_root_dir,
                                         output_dir)
    is_importable, requires_splitting = can_import(output_path)
    if not is_importable:
        logging.warning("[{}] cannot be imported. Skipping.".format(file_name))
        return

    parent_dir = Path(output_path.parent)
    logging.info("Creating directory [{}]".format(parent_dir))
    parent_dir.mkdir(parents=True, exist_ok=True)

    payload = zip_archive.read(file_name)
    if requires_splitting:
        split_pdf_file(file_name, payload, output_path, pdf_split_page_tag)
    else:
        logging.info("Extracting to [{}].".format(output_path))
        post_process_dirs.add(str(output_path.parent))
        output_path.write_bytes(payload)


def import_data(input_files,
                include_files=None,
                remove_root_dir=True,
                output_dir='./data',
                pdf_split_page_tag='pagina'):
    """Reads the contents of the input archive and prepares the files for import.

    Parameters
    ----------
    input_files: iterable of str, required
        The collection containing full path to the zip archives of the files to import.
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
    pdf_split_page_tag: str, optional
        Specifies the token that joins the PDF file name and the page number. Default is 'pagina'.
    """
    post_process_dirs = set()
    for file_path in input_files:
        logging.info("Reading contents of input file {}.".format(input_files))
        with ZipFile(file_path) as zip_archive:
            for f in zip_archive.namelist():
                if (not include_files) or (re.search(include_files, f,
                                                     re.IGNORECASE)):
                    process_archive_content_file(zip_archive, f,
                                                 remove_root_dir, output_dir,
                                                 pdf_split_page_tag,
                                                 post_process_dirs)

    for directory in post_process_dirs:
        enforce_page_order(directory)
        convert_images_to_png(directory)


def parse_arguments():
    parser = ArgumentParser()

    parser.add_argument('--input-file',
                        action='append',
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
        '--pdf-split-page-tag',
        help=
        "Specifies the token that joins the PDF file name and the page number. Default is 'pagina'.",
        default='pagina')
    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO)
    args = parse_arguments()
    import_data(args.input_file, args.include_files, args.remove_root_dir,
                args.output_dir, args.pdf_split_page_tag)
    logging.info("That's all folks!")
