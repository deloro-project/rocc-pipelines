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
