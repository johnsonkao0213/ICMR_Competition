In the directory structure we have a weight file model.pb, run_detection.py that runs testing.
Model related code is located in model.py
TF-lite model weight is model.tflite which can be inferences by NVIDIA TX2

Our os is using Ubuntu 18.04

conda env:
conda env create -f environment.yml -n name
conda activate name

![Model Architecture](model.svg)

The model is based on Yolov4-Double-CSP and do structure prunning and knowledge distillation.