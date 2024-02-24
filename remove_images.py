import os
import pathlib

images_to_delete = []
images_to_stay = []
all_images = []

with open('data/ivslab/test.txt', 'r') as file:
    for line in file:
        images_to_stay.append(line.split('/')[-1].strip())

for image in pathlib.Path('data/ivslab/images').iterdir():
    all_images.append(image.name)

images_to_delete = list(set(all_images).difference(images_to_stay))
for image in images_to_delete:
    os.remove('data/ivslab/images/' + image)

all_labels = []
for image in pathlib.Path('data/ivslab/labels').iterdir():
    all_labels.append(image.name)
labels_to_stay = []
with open('data/ivslab/test.txt', 'r') as file:
    for line in file:
        labels_to_stay.append(line.split('/')[-1].replace('.jpg', '.txt').strip())


labels_to_delete = list(set(all_labels).difference(labels_to_stay))
for label in labels_to_delete:
    os.remove('data/ivslab/labels/' + label)
    


        