sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
sudo apt install python3-pip -y
sudo apt-get install build-essential cmake pkg-config libjpeg-dev libtiff5-dev libpng-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev libpango1.0-dev libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran libhdf5-dev libhdf5-serial-dev libhdf5-103 python3-pyqt5 python3-dev -y
pip3 install -r requirements.txt

# Coral
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install libedgetpu1-std
sudo apt-get install python3-pycoral

# TODO: switch to wget
curl --output file https://raw.githubusercontent.com/google-coral/test_data/master/efficientdet_lite3_512_ptq_edgetpu.tflite
mv yolov8n_full_integer_quant_edgetpu.tflite efficientdet_lite3_512_ptq_edgetpu.tflite
curl https://raw.githubusercontent.com/google-coral/test_data/master/coco_labels.txt > coco_labels.txt
