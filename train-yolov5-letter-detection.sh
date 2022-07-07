#!/bin/bash

# Script arguments
SERVER=$1
USER=$2
PASSWORD=$3
MODEL=$4

# Constants
YOLO_DIR=/var/training/yolov5
EPOCHS=(300 600 900)


# Create directory where to store training data.
mkdir -p /var/training/data

# Create directory where to store experiment results.
mkdir -p /var/training/experiments

# Navigate to data directory.
cd /var/training/data

# Remove old data if present.
rm -rf *.zip

# Secure copy the training data.
sshpass -p $PASSWORD scp $USER@$SERVER:/var/export/yolov5-annotations-*.zip

# Navigate to the yolov5 directory
cd $YOLO_DIR

# Iterate training params and train for each combination.
for num_epochs in "${EPOCHS[@]}" do
    for file in /var/training/data/*.zip; do
        # Remove old training data if present.
        rm -rf yolo-export deloro
        # Extract training data.
        unzip $file -d .
        # Rename yolo-export to deloro.
        mv yolo-export deloro
        # Fix paths in YAML file
        sed -i 's/yolo-export\//data\/deloro\//g' deloro/characters/characters.yaml
        # Get the resolution from file name by splitting the file name by '-' and taking the 3rd field.
        img_size=$(echo $file | cut -d'-' -f3)
        # Get the image type. First, split by '.' to remove the extension, and then split by '-' and take the 4th field.
        img_type=$(echo $file | cut -d'.' -f1 | cut -d'-' -f4)
        # Activate virtual environment.
        cd $YOLO_DIR
        source .venv/bin/activate
        # Start training
        python train.py --img $img_size --batch-size -1 --epochs $num_epochs --data data/deloro/characters/characters.yaml --device cpu --weights $MODEL
        # Deactivate virtual environment.
        deactivate

	# Export run results to /var/training/experiments.
	# Navigate to results directory.
	cd $YOLO_DIR/runs/train
	# Get model name without extension.
	$model_name=$(echo $MODEL | cut -d'.' -f1)
	# Build the file name of the archive of current results.
	$experiment_archive="${model_name}-epochs-${num_epochs}-size-${img_size}-type-${img_type}.zip"
	# Archive the run results.
	zip -r $experiment_archive exp/
	mv -f $experiment_archive /var/training/experiments
	# Remove the run results
	rm -rf exp
    done
done
