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
    python export-yolov5-annotations.py characters --db-server $DB_SERVER --db-name $DB_NAME --user $USER --password $PASSWORD --image-size $IMG_SIZE $IMG_SIZE --binary-read;
else
    python export-yolov5-annotations.py characters --db-server $DB_SERVER --db-name $DB_NAME --user $USER --password $PASSWORD --image-size $IMG_SIZE $IMG_SIZE;
fi

# Deactivate virtual environment
deactivate;

# Archive exported data
zip -r yolov5-annotations-${IMG_SIZE}-${IMG_TYPE}.zip yolo-export/;

# Move the archive to /var/export/
mv -f yolov5-annotations-${IMG_SIZE}-${IMG_TYPE}.zip /var/export/;

# Cleanup
rm -rf yolo-export;
