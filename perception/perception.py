import ADCPlatform
import time
from PIL import Image
import numpy
import torch

import perception.DrivingDetection as detection

import sys
sys.path.append("../")
import control.pid as pid
from yolox.data.datasets import COCO_CLASSES

def convert_image_to_numpy_ndarray(imageframe_byte):
	#image2 = Image.fromarray(array) # image2 is a PIL image,array is a numpy
	#array
   return numpy.array(Image.open(imageframe_byte))

def run(perceptionFlag, data, PerceptionArgs):
    # data : a dict of 4 elements
    # including "control", "landLine", "radar" and "image"
    # PerceptionArgs : a dict of 2 elements
    # including "predictor" and "args"
    if not perceptionFlag:
        return None

    img = convert_image_to_numpy_ndarray(data["image"].byte)
    # print(img.shape)
    detection.driving_runtime(PerceptionArgs["predictor"], None, img, PerceptionArgs["args"])

    return None


