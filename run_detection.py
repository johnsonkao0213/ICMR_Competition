import tensorflow as tf
import numpy as np
import csv
import cv2 as cv
import time
import argparse

if __name__=="__main__":
    pb_path=r'model.pb'
    input_shape=[640,640]

    parser = argparse.ArgumentParser()

    parser.add_argument("image_list", help="Prints the supplied argument.")
    parser.add_argument("output_path")

    args = parser.parse_args()

    with tf.Graph().as_default():
        output_graph_def = tf.GraphDef()
        with open(pb_path, "rb") as f:
            output_graph_def.ParseFromString(f.read())
            tf.import_graph_def(output_graph_def, name="")
        sess = tf.Session()
        sess.run(tf.global_variables_initializer())
        
        input = sess.graph.get_tensor_by_name("input:0")
        output = sess.graph.get_tensor_by_name("output:0")

        img_names = []
        with open(args.image_list, 'r') as file:
            for line in file:
                img_names.append(line.strip())

        names = []
        predictions = []
        time_per_image = []
        for name in img_names:  
            img = cv.imdecode(np.fromfile(name, np.uint8), -1)[:, :, :3]
            img = cv.resize(img, tuple(input_shape[::-1]))
            img_ = np.expand_dims(img[:, :, ::-1], 0).astype(np.float16) / 255.

            t1=time.clock()
            pred = sess.run(output, feed_dict={input: img_})
            time_per_image.append(time.clock()-t1)
            np.set_printoptions(suppress=True)
            predictions.append(pred)
            names.append(name)
            print(name)

        with open(args.output_path + "/submission.csv", "w", newline="") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(["image_filename", "label_id", "x",
                            "y", "w", "h", "confidence"])
                
            for i, prediction in enumerate(predictions):
                for entry in prediction:
                    writer.writerow(
                        [
                            names[i],
                            int(entry[-1]),
                            entry[0],
                            entry[1],
                            entry[2],
                            entry[3],
                            entry[-2],
                        ]
                    )    
        
        print('Average time:', sum(time_per_image) / len(time_per_image))

        


