import time
from PIL import Image
import numpy

import perception.DrivingDetection as detection

import sys
sys.path.append("../")

class DistanceData:
    def __init__(self):
        self.distance_left = float('inf')
        self.distance_mid =  float('inf')
        self.distance_right = float('inf')
    
    def __len__(self):
        return 3
    
    def get_distance(self):
        return self.distance_left, self.distance_mid, self.distance_right
    
    def set_distance_left(self, dis):
        self.distance_left = dis

    def set_distance_mid(self, dis):
        self.distance_mid = dis

    def set_distance_right(self, dis):
        self.distance_right = dis


def convert_image_to_numpy_ndarray(imageframe_byte):
    return numpy.array(Image.open(imageframe_byte))


def run(perceptionFlag, data, PerceptionArgs, distanceData, MyCar):
    # data : a dict of 4 elements
    # including "control", "landLine", "radar" and "image"
    # PerceptionArgs : a dict of 2 elements
    # including "predictor" and "args"
    if not perceptionFlag:
        return None

    time.sleep(0.5)
    while True:
        try:
            img = convert_image_to_numpy_ndarray(data["image"].byte)
            result_left, result_mid, result_right = detection.driving_runtime(predictor=PerceptionArgs["predictor"], 
                                                                        vis_folder=None, 
                                                                        image=img, 
                                                                        args=PerceptionArgs["args"], 
                                                                        MyCar=MyCar)
            if MyCar.midlane == 7.5:
                distanceData.set_distance_left(float('inf'))
            else:
                distanceData.set_distance_left(result_left.item())

            if MyCar.midlane == -7.5:
                distanceData.set_distance_right(float('inf'))
            else:
                distanceData.set_distance_right(result_right.item())
            distanceData.set_distance_mid(result_mid.item())
        except:
            pass

    return None


