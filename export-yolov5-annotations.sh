DB_SERVER=$1
DB_NAME=$2
USER=$3
PASSWORD=$4
IMG_SIZE=${5:-2048}

rm -rf yolo-export
source .venv/bin/activate;
python export-yolov5-annotations.py --db-server $DB_SERVER --db-name $DB_NAME --user $USER --password $PASSWORD --image-size $IMG_SIZE $IMG_SIZE;
deactivate;
zip -r yolov5-annotations.zip yolo-export/letters;
mv -f yolov5-annotations.zip /var/export/
rm -rf yolo-export
