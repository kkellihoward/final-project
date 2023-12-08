#!/bin/bash

# Update package information
#sudo apt-get update

# Upgrade pip
#python3 -m pip install --user --upgrade pip

# Create and activate a virtual environment
python3 -m venv ~/tflite
source ~/tflite/bin/activate

# Change to the specified directory
cd /home/pi/examples/lite/examples/object_detection/raspberry_pi

# Erase all data in output.txt
> output.txt

# Run the first Python script (detect.py) in a separate terminal
detector="python3 detect.py --object"
lxterminal --command="$detector $1"

# Wait for 5 seconds
sleep 5

# Install library for code
pip install RPi.GPIO smbus pyttsx3

# Run the second Python script (main.py)
python3 main.py $1

# Deactivate the virtual environment
deactivate
