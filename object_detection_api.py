# IMPORTS

import numpy as np
import os
import six.moves.urllib as urllib
import tarfile
import tensorflow as tf
import json

# if tf.__version__ != '1.4.0':
#   raise ImportError('Please upgrade your tensorflow installation to v1.4.0!')

# ENV SETUP  ### CWH: remove matplot display and manually add paths to references

# Object detection imports
from object_detection.utils import label_map_util    ### CWH: Add object_detection path

# Model Preparation

# What model to download.
MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('object_detection/data', 'mscoco_label_map.pbtxt') ### CWH: Add object_detection path

NUM_CLASSES = 90


# Download Model
opener = urllib.request.URLopener()
opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
tar_file = tarfile.open(MODEL_FILE)
for file in tar_file.getmembers():
  file_name = os.path.basename(file.name)
  if 'frozen_inference_graph.pb' in file_name:
    tar_file.extract(file, os.getcwd())


# Load a (frozen) Tensorflow model into memory.
detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)


# Helper code
def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)

with detection_graph.as_default():
  with tf.Session(graph=detection_graph) as sess:
    # Definite input and output Tensors for detection_graph
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
    # Each box represents a part of the image where a particular object was detected.
    detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
    # Each score represent how level of confidence for each of the objects.
    # Score is shown on the result image, together with the class label.
    detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
    detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')
# added to put object in JSON
class Object(object):
    def __init__(self):
        self.name="webrtcHacks TensorFlow Object Detection REST API"

    def toJSON(self):
        return json.dumps(self.__dict__)

def get_objects(image, threshold=0.5):
    image_np = load_image_into_numpy_array(image)
    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)
    # Actual detection.

      # Run inference
    output_dict = sess.run(
        [detection_boxes, detection_scores, detection_classes, num_detections],
        feed_dict={image_tensor: image_np_expanded})

      # all outputs are float32 numpy arrays, so convert types as appropriate
    num = int(output_dict['num_detections'][0])
      # num = (output_dict['num_detections'][0])
    classes = output_dict['detection_classes'][0].astype(np.int64)
    boxes = output_dict['detection_boxes'][0]
    scores = output_dict['detection_scores'][0]

    obj_above_thresh = sum(n > threshold for n in scores)
    print("detected %s objects in image above a %s score" % (obj_above_thresh, threshold))
    output = []

      # Add some metadata to the output
    item = Object()
    item.version = "0.0.1"
    item.numObjects = int(obj_above_thresh)
    item.threshold = threshold
      # print(item.toJSON())
      # print(type(obj_above_thresh), obj_above_thresh.shape)
    output.append(item)

    for c in range(0, len(classes)):
      class_name = category_index[classes[c]]['name']
      if scores[c] >= threshold:      # only return confidences equal or greater than the threshold
          print(" object %s - score: %s, coordinates: %s" % (class_name, scores[c], boxes[c]))
          item = Object()
          item.name = 'Object'
          item.class_name = class_name
          item.score = float(scores[c])
          item.y = float(boxes[c][0])
          item.x = float(boxes[c][1])
          item.height = float(boxes[c][2])
          item.width = float(boxes[c][3])
            
          output.append(item)
    outputJson = json.dumps(output, default = lambda x: x.__dict__)
    return outputJson

def run(image, threshold=0.5):
  image_np = load_image_into_numpy_array(image)
  # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
  image_np_expanded = np.expand_dims(image_np, axis=0)
  return run_inference_for_single_image(image_np_expanded, detection_graph, threshold)

def run_inference_for_single_image(image, graph, threshold):
  with graph.as_default():
    with tf.Session() as sess:
      # Get handles to input and output tensors
      ops = tf.get_default_graph().get_operations()
      all_tensor_names = {output.name for op in ops for output in op.outputs}
      tensor_dict = {}
      for key in [
          'num_detections', 'detection_boxes', 'detection_scores',
          'detection_classes', 'detection_masks'
      ]:
        tensor_name = key + ':0'
        if tensor_name in all_tensor_names:
          tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
              tensor_name)
      if 'detection_masks' in tensor_dict:
        # The following processing is only for single image
        detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
        detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
        # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
        real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
        detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
        detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
            detection_masks, detection_boxes, image.shape[1], image.shape[2])
        detection_masks_reframed = tf.cast(
            tf.greater(detection_masks_reframed, 0.5), tf.uint8)
        # Follow the convention by adding back the batch dimension
        tensor_dict['detection_masks'] = tf.expand_dims(
            detection_masks_reframed, 0)
      image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

      # Run inference
      output_dict = sess.run(tensor_dict,
                             feed_dict={image_tensor: image})

      # all outputs are float32 numpy arrays, so convert types as appropriate
      num = int(output_dict['num_detections'][0])
      # num = (output_dict['num_detections'][0])
      classes = output_dict['detection_classes'][0].astype(np.int64)
      boxes = output_dict['detection_boxes'][0]
      scores = output_dict['detection_scores'][0]

      obj_above_thresh = sum(n > threshold for n in scores)
      print("detected %s objects in image above a %s score" % (obj_above_thresh, threshold))
      output = []

      # Add some metadata to the output
      item = Object()
      item.version = "0.0.1"
      item.numObjects = int(obj_above_thresh)
      item.threshold = threshold
      # print(item.toJSON())
      # print(type(obj_above_thresh), obj_above_thresh.shape)
      output.append(item)

      for c in range(0, len(classes)):
        class_name = category_index[classes[c]]['name']
        if scores[c] >= threshold:      # only return confidences equal or greater than the threshold
            print(" object %s - score: %s, coordinates: %s" % (class_name, scores[c], boxes[c]))
            
            # print(type(class_name), type(scores[c].shape), type(boxes[c][0].shape), type(boxes[c][1].shape), type(boxes[c][2].shape), type(boxes[c][3].shape))
            # print((class_name), (scores[c].shape), (boxes[c][0].shape), (boxes[c][1].shape), (boxes[c][2].shape), (boxes[c][3].shape))
            # print((class_name), (scores[c]), (boxes[c][0]), (boxes[c][1]), (boxes[c][2]), (boxes[c][3]))

            item = Object()
            item.name = 'Object'
            item.class_name = class_name
            item.score = float(scores[c])
            item.y = float(boxes[c][0])
            item.x = float(boxes[c][1])
            item.height = float(boxes[c][2])
            item.width = float(boxes[c][3])
            
            output.append(item)
            # print(item.toJSON())

      # if 'detection_masks' in output_dict:
      #   output_dict['detection_masks'] = output_dict['detection_masks'][0]
      # outputJson = json.dumps([ob.__dict__ for ob in output])
      outputJson = json.dumps(output, default = lambda x: x.__dict__)
      return outputJson