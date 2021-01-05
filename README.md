# Romanian Old Cyrillic Corpus pipelines #

The pipelines (a fancy name for scripts and tools) from this repository are used to setup the normal workflow of the ROCC.

## Repository structure ##

- `python` directory contains pipelines (a.k.a. scripts) written in Python
- `java` directory contains the source code of the tools written in Java

## Pipelines ##

### Import Data ###

- **Script name**: [`import-data.py`](./python/import-data.py)
- **Description**: This script reads the contents of the archived Google Drive directory containing raw data and moves the data into a hierarchical structure with normalized path names. Additionally, it splits the PDF files into images of each page.
