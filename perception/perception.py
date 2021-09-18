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
   return numpy.array(Image.open(imageframe_byte))

def run(perceptionFlag, data, PerceptionArgs, distance):
    # data : a dict of 4 elements
    # including "control", "landLine", "radar" and "image"
    # PerceptionArgs : a dict of 2 elements
    # including "predictor" and "args"
    if not perceptionFlag:
        return None

    time.sleep(0.5)
    while True:
        img = convert_image_to_numpy_ndarray(data["image"].byte)
        result = detection.driving_runtime(PerceptionArgs["predictor"], None, img, PerceptionArgs["args"])
        distance = {"data": result.item()}
        # print("distance : ", distance.item())

    return None


