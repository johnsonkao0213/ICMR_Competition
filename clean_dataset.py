import pathlib
import argparse
from random import sample

path_to_images = pathlib.Path('data/ivslab_train/JPEGImages/All')


def get_file_names(path):
    full_path = path_to_images / path
    files = []
    for file in pathlib.Path(full_path).iterdir():
        files.append(file.name)
    return files


def get_every_n(array, n):
    return array[0::n]


parser = argparse.ArgumentParser()
parser.add_argument('--keep_every_n', type=int)
opt = parser.parse_args()
folders = []
keep_n = []
special_images = []
final_images = []


with open('dirs.txt', 'r') as file:
    for line in file:
        folders.append(line.split(':')[0].strip())
        keep_n.append(int(line.split(':')[1].strip()))

with open('special.txt', 'r') as file:
    for line in file:
        special_images.append(line.strip())

special_images = set(special_images)
for idx, folder in enumerate(folders):
    images_to_clean = get_file_names(folder)
    images_to_clean.sort()
    images_to_keep = get_every_n(images_to_clean, keep_n[idx])

    if special_images:
        images_to_keep.extend(special_images.intersection(images_to_clean))

    final_images.extend(images_to_keep)

test = sample(final_images, int(len(final_images)*0.15))
train = set(final_images).difference(test)

with open('train.txt', 'w') as file:
    for image in train:
        file.write(image + '\n')

with open('test.txt', 'w') as file:
    for image in test:
        file.write(image + '\n')
