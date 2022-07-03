DB_SERVER=$1
DB_NAME=$2
USER=$3
PASSWORD=$4
IMG_SIZE=${5:-1280}


# Remove old export directory if exists
rm -rf yolo-export;

# Activate virtual environment
source .venv/bin/activate;

# Export annotations
python export-yolov5-annotations.py characters --db-server $DB_SERVER --db-name $DB_NAME --user $USER --password $PASSWORD --image-size $IMG_SIZE $IMG_SIZE;

# Deactivate virtual environment
deactivate;

# Archive exported data
zip -r yolov5-annotations-${IMG_SIZE}.zip yolo-export/;

# Move the archive to /var/export/
mv -f yolov5-annotations-${IMG_SIZE}.zip /var/export/;

# Cleanup
rm -rf yolo-export;
