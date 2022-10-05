DB_SERVER=$1
DB_NAME=$2
USER=$3
PASSWORD=$4
IMG_SIZE=${5:-1280}
IMG_TYPE=$6

echo "Exporting images at ${IMG_SIZE}x${IMG_SIZE} in ${IMG_TYPE}."

# Remove old export directory if exists
rm -rf yolo-export;

# Activate virtual environment
source .venv/bin/activate;

# Export annotations
if [ "$IMG_TYPE" = 'grayscale' ]; then
    python export-yolov5-annotations-on-full-images.py \
	   --db-server $DB_SERVER \
	   --db-name $DB_NAME \
	   --user $USER \
	   --password $PASSWORD \
	   --image-size $IMG_SIZE $IMG_SIZE \
	   --blur-negative-samples \
	   --binary-read \
	   --log-level ERROR;
else
    python export-yolov5-annotations-on-full-images.py \
	   --db-server $DB_SERVER \
	   --db-name $DB_NAME \
	   --user $USER \
	   --password $PASSWORD \
	   --image-size $IMG_SIZE $IMG_SIZE \
	   --blur-negative-samples \
	   --log-level ERROR;
fi

# Deactivate virtual environment
deactivate;

ARCHIVE_FILE=yolov5-annotations-${IMG_SIZE}-${IMG_TYPE}.zip
# Archive exported data
echo "Compressing exported data to ${ARCHIVE_FILE}."
zip -r $ARCHIVE_FILE yolo-export/;

# Move the archive to /var/export/
echo "Moving ${ARCHIVE_FILE} to /var/export/."
mv -f yolov5-annotations-${IMG_SIZE}-${IMG_TYPE}.zip /var/export/;

# Cleanup
echo "Cleaning up export directory."
rm -rf yolo-export;

echo "Done."
