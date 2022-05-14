#!/bin/bash

YOLO_DIR=${1:-~/yolov5/}
ARCHIVE_PATH=${2:-/var/export/yolov5-annotations.zip}
IMG_SIZE=${3:-1024}
EPOCHS=${4:-1}
MODEL=${5:-yolov5s.pt}


cd $YOLO_DIR
cd data

# Remove old data if present
rm -rf yolov5-annotations.zip yolo-export deloro

# Copy and extract training data
cp $ARCHIVE_PATH .
unzip yolov5-annotations.zip -d .

# Rename yolo-export to deloro
mv yolo-export deloro

# Fix paths in YAML file
sed -i 's/yolo-export\//data\/deloro\//g' deloro/letters/letters.yaml

# Activate virtual environment
cd $YOLO_DIR
source .venv/bin/activate

# Start training
python train.py --img $IMG_SIZE --batch-size -1 --epochs $EPOCHS --data data/deloro/letters/letters.yaml --device cpu --weights $MODEL

# Deactivate virtual environment
deactivate
