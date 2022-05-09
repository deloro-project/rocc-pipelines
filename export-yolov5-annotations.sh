rm -rf yolo-export
source .venv/bin/activate;
python export-yolov5-annotations.py --db-server $1 --db-name $2 --user $3 --password $4;
deactivate;
zip -r yolov5-annotations.zip yolo-export/letters;
mv -f yolov5-annotations.zip /var/export/
rm -rf yolo-export
