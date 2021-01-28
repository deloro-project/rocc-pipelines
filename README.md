# Romanian Old Cyrillic Corpus pipelines #

The pipelines (a fancy name for scripts and tools) from this repository are used to setup the normal workflow of the ROCC.

## Repository structure ##

- `python` directory contains pipelines (a.k.a. scripts) written in Python
- `java` directory contains the source code of the tools written in Java

## Running Python scripts ##

The recommended way of running the python pipelines is to create a virtual environment in order to keep the server clean.

Note: *All the pipelines require `python3` to be installed*.

### Setting up a Python virtual environment ###

To setup the virtual environment used for running the scripts follow these steps:
1. Clone this repository,
2. Navigate to the directory where the repository was cloned; e.g. `cd ~/Git/rocc-pipelines`,
3. Open a terminal window and issue the following command: `python3 -m venv .venv`. This will create a virtual environment in the `.venv` directory,
4. Activate the virtual environment using `source .venv/bin/activate`,
5. Update the environment using `pip install -U pip setuptools wheel`,
6. Install the required packages using `pip install -r requirements.txt`
7. Optional - deactivate the environment using `deactivate`
8. Close the terminal window.

### Running a pipeline script ###

To run a python script included in this repository follow these steps:
1. Open a terminal window and navigate to the directory where the repository was cloned; e.g. `cd ~/Git/rocc-pipelines`,
2. Activate the virtual environment mentioned earlier using `source .venv/bin/activate`
3. Navigate to `python` directory using `cd python`,
4. Run the script using `python <script-name> <arguments>` where:
   1. `<script-name>` is the name of the script you want to run
   2. `<arguments>` represents the arguments given to the script.

## Pipelines ##

### Import Data ###

- **Script name**: [`import-data.py`](./python/import-data.py)
- **Description**: This script reads the contents of the archived Google Drive directory containing raw data and moves the data into a hierarchical structure with normalized path names. Additionally, it splits the PDF files into images of each page.

### Usage ###

To get the list of the script parameters with their description call the script with either `-h` or `--help` *after activating the virtual environment*.

```sh
python import-data.py --help
```

The output of the command above should look like the following:
```sh
usage: import-data.py [-h] [--input-file INPUT_FILE] [--include-files INCLUDE_FILES]
                      [--remove-root-dir] [--output-dir OUTPUT_DIR]
                      [--pdf-split-page-tag PDF_SPLIT_PAGE_TAG]

optional arguments:
  -h, --help            show this help message and exit
  --input-file INPUT_FILE
                        Full path of the input archive (zip) file.
  --include-files INCLUDE_FILES
                        The regex pattern for files to include
  --remove-root-dir     Specifies whether to remove the root directory of the files from the input.
  --output-dir OUTPUT_DIR
                        The root directory where to extract the contents of the archive.
  --pdf-split-page-tag PDF_SPLIT_PAGE_TAG
                        Specifies the token that joins the PDF file name and the page number. Default
                        is 'pagina'.
```

Examples:
- To import all the contents of the archive file located at `~/Downloads/Data.zip` into the directory `/data/rocc/data` use:
```sh
python import-data.py --input-file ~/Downloads/Data.zip --output-dir /data/rocc
```
- To import all the contents of the archive file located at `~/Downloads/Data.zip` into the directory `/data/rocc/` use:
```sh
python import-data.py --input-file ~/Downloads/Data.zip --output-dir /data/rocc --remove-root-dir
```
- To import only files that contain `uncial` in their name from the archive file located at `~/Downloads/Data.zip` into the directory `/data/rocc` use:
```sh
python import-data.py --input-file ~/Downloads/Data.zip --output-dir /data/rocc --remove-root-dir --inclide-files uncial
```
In this case, `uncial` is a regex pattern; you can specify more complex patterns according to your needs.

- By default the script will split pdf files into images named `<pdf-file-name-without-extension>-pagina-<page-number>.png`. If you want to change the token to be `pag` call the script with the desired value for `--pdf-split-page-tag` parameter:
```sh
python import-data.py --input-file ~/Downloads/Data.zip --output-dir /data/rocc --remove-root-dir --pdf-split-page-tag pag
```
- To import multiple zip archives repeat the `--inpug-file` argument for each file to import:
```sh
python import-data.py --input-file ~/Downloads/Data-001.zip --input-file ~/Downloads/Data-002.zip --output-dir /data/rocc

```
