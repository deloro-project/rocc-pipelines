# Romanian Old Cyrillic Corpus pipelines #

The pipelines (a fancy name for scripts and tools) from this repository are used to setup the normal workflow of the ROCC.

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

#### Important: Setting up virtual environment on production server  ####
For some reason, when setting up virtual environment on production server `pip` fails to install package `psycopg2`.

The workaround is to:
1. Open `requirements.txt` file in any editor
2. Comment the line containing `psycopg2` and save the file.
3. Activate the virtual environment
4. Run `pip install psycopg2-binary`
5. Run `pip install -r requirements.txt`

### Running a pipeline script ###

To run a python script included in this repository follow these steps:
1. Open a terminal window and navigate to the directory where the repository was cloned; e.g. `cd ~/Git/rocc-pipelines`,
2. Activate the virtual environment mentioned earlier using `source .venv/bin/activate`
3. Run the script using `python <script-name> <arguments>` where:
   1. `<script-name>` is the name of the script you want to run
   2. `<arguments>` represents the arguments given to the script.

## Pipelines ##

### Import Data ###

- **Script name**: [`import-data.py`](./import-data.py)
- **Description**: This script reads the contents of the archived Google Drive directory containing raw data and moves the data into a hierarchical structure with normalized path names. Additionally, it splits the PDF files into images of each page.

#### Usage ####

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

### Export Annotations ###

- **Script name**: [export-annotations.py](./export-annotations.py)
- **Description**: This script reads letter annotations from database by querying the view `letter_annotations` and prepares the annotations for export by copying the images of the annotated pages into the export directory and saving the annotations into a CSV file in the same directory.

#### Usage  ####

To get the list of the script parameters with their description call the script with either `-h` or `--help` *after activating the virtual environment*.

```sh
python export-annotations.py --help
```

The output of the command above should look like the following:
```sh
usage: export-annotations.py [-h] --db-server DB_SERVER --db-name DB_NAME --user USER --password PASSWORD [--port PORT] [--output-dir OUTPUT_DIR] [--letter-annotations-file LETTER_ANNOTATIONS_FILE]
                             [--line-annotations-file LINE_ANNOTATIONS_FILE] [--images-root IMAGES_ROOT] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Arguments for exporting annotations.

optional arguments:
  -h, --help            show this help message and exit
  --db-server DB_SERVER
                        Name or IP address of the database server.
  --db-name DB_NAME     The name of the database to connect to.
  --user USER           The username under which to connect to the database.
  --password PASSWORD   The password of the user.
  --port PORT           The port of the database server. Default value is 5432.
  --output-dir OUTPUT_DIR
                        The path of the output directory. Default value is './export'.
  --letter-annotations-file LETTER_ANNOTATIONS_FILE
                        Name of the CSV file containing the annotations.
  --line-annotations-file LINE_ANNOTATIONS_FILE
                        Name of the CSV file containing the annotations.
  --images-root IMAGES_ROOT
                        Images root directory.
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The level of details to print when running.
```

To run the script, *activate the virtual environment* and then issue the following command
```sh
python export-annotations.py \
       --db-server <database-server> \
       --db-name <database-name> \
       --user <username> \
       --password <password>
```
where:
- `<database-server>` is the IP Address or name of the database server,
- `<database-name>` is the name of the PostgreSQL database containing `letter_annotations` view,
- `<username>` is the user which has access to read rows from the view, and
- `<password>` is the password of the above user.

The command above will export export the data into a subdirectory named `export` of the directory where the script is executed. To change the output directory specify a value for the `--output-dir` parameter.

The contents of the output directory are as follows:
- a CSV file containing letter annotations and their metadata. The default name of the file is `letter-annotations.csv`; if you want to change this name provide a value for `--letter-annotations-file` parameter.
- a CSV file containing line annotations and their metadata. The default name of the file is `line-annotations.csv`; if you want to change this name provide a value for `--line-annotations-file` parameter.
- several directories containing the images of the annotated pages such that the path of the images corresponds to the path specified in the column `page_image_file` from the CSV file.


### Export Common Lexii ###

- **Script name**: [export-common-lexicon.py](./export-common-lexicon.py)
- **Description**: This script reads line annotations from database and integral transcribed files for each collection (where available), groups data into periods of 50 years and builds lexicon for each period.

#### Usage  ####

To get the list of the script parameters with their description call the script with either `-h` or `--help` *after activating the virtual environment*.

```sh
python export-common-lexicon.py --help
```

The output of the command above should look like the following:
```sh
usage: export-common-lexicon.py [-h] --db-server DB_SERVER --db-name DB_NAME --user USER --password PASSWORD [--port PORT] [--output-dir OUTPUT_DIR] [--write-header]
                                [--size-stats-file SIZE_STATS_FILE] [--terms-per-periods-file TERMS_PER_PERIODS_FILE] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Export common lexicon

options:
  -h, --help            show this help message and exit
  --db-server DB_SERVER
                        Name or IP address of the database server.
  --db-name DB_NAME     The name of the database to connect to.
  --user USER           The username under which to connect to the database.
  --password PASSWORD   The password of the user.
  --port PORT           The port of the database server. Default value is 5432.
  --output-dir OUTPUT_DIR
                        The path of the output directory. Default value is './export'.
  --write-header        Specifies whether to add header row to lexicon export files.
  --size-stats-file SIZE_STATS_FILE
                        The name of the file containing size statistics.
  --terms-per-periods-file TERMS_PER_PERIODS_FILE
                        The name of the file tracing lexicon terms per periods.
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The level of details to print when running.
```

To run the script, *activate the virtual environment* and then issue the following command
```sh
python export-common-lexicon.py \
       --db-server <database-server> \
       --db-name <database-name> \
       --user <username> \
       --password <password>
```
where:
- `<database-server>` is the IP Address or name of the database server,
- `<database-name>` is the name of the PostgreSQL database containing `letter_annotations` view,
- `<username>` is the user which has access to read rows from the view, and
- `<password>` is the password of the above user.

The command above will export export the data into a subdirectory named `lexii` of the directory where the script is executed. To change the output directory specify a value for the `--output-dir` parameter.

The contents of the output directory are as follows:
- several csv files (one per each 50 year period) containing vocabulary tokens, one per line.
- a statistics file named `size-stats.csv` which contains the size of the vocabulary for each period; to change this name provide a value for `--size-stats-file` parameter.
- a file named `lexicon-per-periods.csv` which contains the terms that appear in more than one period and the periods they appear in; to change this name provide a value for `terms-per-periods-file` parameter.

### Train Yolo v5 detection of letters ###

- **Script name**: [train-yolov5-letter-detection.sh](./train-yolov5-letter-detection.sh)
- **Description**: This script unzips the export of letter annotations for Yolo v5 and trains a Yolo v5 model on the exported data.

#### Usage ####

To run the script issue the following command:
```sh
./train-yolov5-letter-detection.sh <yolo-directory> <archive-path> <image-size> <epochs> <model>
```
where:
- `<yolo-directory>` is the path of the `yolov5` directory,
- `<archive-path>` is the path of the zip file containing exported annotations,
- `<image-size>` is the size of the exported images,
- `<epochs>` is the number of epochs for training,
- `<model>` is the name of the yolo model; can be one of:
  - `yolov5s.pt`
  - `yolov5m.pt`
  - `yolov5l.pt`
  - `yolov5x.pt`.
