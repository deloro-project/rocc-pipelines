#!/bin/bash

# Script arguments
SERVER=$1
USER=$2
MODEL=$3

# Constants
YOLO_DIR=~/training/yolov5
EPOCHS=(300 600 900)
DATA_DIR=~/training/data
EXPERIMENTS_DIR=~/training/experiments

# Create training directory.
mkdir -p  ~/training

# Create directory where to store training data.
mkdir -p $DATA_DIR

# Create directory where to store experiment results.
mkdir -p $EXPERIMENTS_DIR

# Navigate to data directory.
cd $DATA_DIR

# Remove old data if present.
echo "Cleaning directory ${DATA_DIR}."
rm -rf *.zip

# Secure copy the training data.
echo "Copying training sets to ${DATA_DIR}."
scp $USER@$SERVER:/var/export/yolov5-annotations-*.zip $DATA_DIR

# Navigate to the yolov5 directory
cd $YOLO_DIR

# Iterate training params and train for each combination.
echo "Start training."
for num_epochs in "${EPOCHS[@]}"
do
    for file in $DATA_DIR/*.zip; do
	echo "Training on set ${file} for ${num_epochs} epochs."
        cd $YOLO_DIR/data

	echo "Removing old training data."
        rm -rf yolo-export deloro *.zip

	echo "Uncompressing ${file} into ${YOLO_DIR}/data directory."
        unzip $file -d .
	echo "Preparing training set."
        # Rename yolo-export to deloro.
        mv yolo-export deloro
        # Fix paths in YAML file
        sed -i 's/yolo-export\//data\/deloro\//g' deloro/characters/characters.yaml
        # Get the resolution from file name by splitting the file name by '-' and taking the 3rd field.
        img_size=$(echo $file | cut -d'-' -f3)
        # Get the image type. First, split by '.' to remove the extension, and then split by '-' and take the 4th field.
        img_type=$(echo $file | cut -d'.' -f1 | cut -d'-' -f4)
	echo "Start training for ${num_epochs} epochs on ${img_type} images of size ${img_size}x${img_size}."

        # Activate virtual environment.
        cd $YOLO_DIR
        source .venv/bin/activate
        # Start training
        python train.py --img $img_size --batch-size -1 --epochs $num_epochs --data data/deloro/characters/characters.yaml --device cpu --weights $MODEL
        # Deactivate virtual environment.
        deactivate

	# Export run results to $EXPERIMENTS_DIR.
	# Navigate to results directory.
	cd $YOLO_DIR/runs/train
	# Get model name without extension.
	$model_name=$(echo $MODEL | cut -d'.' -f1)
	# Build the file name of the archive of current results.
	$experiment_archive="${model_name}-epochs-${num_epochs}-size-${img_size}-type-${img_type}.zip"
	# Archive the run results.
	zip -r $experiment_archive exp/
	mv -f $experiment_archive $EXPERIMENTS_DIR
	# Remove the run results
	rm -rf exp
    done
done
