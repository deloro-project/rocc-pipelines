#!/usr/bin/env bash
DB_SERVER=$1
DB_NAME=$2
USER=$3
PASSWORD=$4

echo "Exporting letter annotations."
# Remove old export directory if exists
rm -rf export

# Activate virtual environment
source .venv/bin/activate;

python export-letter-annotations.py \
       --db-server $DB_SERVER \
       --db-name $DB_NAME \
       --user $USER \
       --password $PASSWORD \
       --min-samples-per-class 1000 \
       --log-level ERROR;

# Deactivate virtual environment
deactivate;

ARCHIVE_FILE=letter-classification-export.zip
# Archive exported data
echo "Compressing exported data to ${ARCHIVE_FILE}."
zip -r $ARCHIVE_FILE export/;

# Move the archive to /var/export/
echo "Moving ${ARCHIVE_FILE} to /var/export/."
mv -f $ARCHIVE_FILE /var/export/;

# Cleanup
echo "Cleaning up export directory."
rm -rf export;

echo "Done."
