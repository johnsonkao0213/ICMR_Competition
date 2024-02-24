In the directory structure, we have a weight file model.pb, run_detection.py that runs testing.
Model related code is located in model.py
TF-lite model weight is model.tflite which can be inferences by NVIDIA TX2

**Pretrained Model Weight:** [weight link](https://drive.google.com/drive/folders/11qAoGvsGZqcshxxz8QZaB86YkmYk7xPq?usp=sharing)

Our OS is using Ubuntu 18.04

conda env:
conda env create -f environment.yml -n name
conda activate name

![Model Architecture](model.svg)

The model is based on Yolov4-Double-CSP and does structure pruning and knowledge distillation.
