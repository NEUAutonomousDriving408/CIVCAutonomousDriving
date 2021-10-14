#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author : HuangXinghui

import time
from PIL import Image
import numpy
import sys
sys.path.append("../")

import perception.DrivingDetection as detection



class DistanceData(object):
    """
    The distance data class of autonomous driving vehicle the 
    three lane vehicles in front of it.
    
    Attributes:
        distance_left: distance between the left front vehicle and current vehicle
        distance_mid: distance between the middle front vehicle and current vehicle
        distance_right: distance between the right front vehicle and current vehicle
    """
    
    def __init__(self):
        """ Initilizing three distances to infinity """
        self.distance_left = float('inf')
        self.distance_mid =  float('inf')
        self.distance_right = float('inf')
    
    def get_distance(self):
        """ Return the three distances to tuple type """
        return self.distance_left, self.distance_mid, self.distance_right
    
    def __len__(self):
        """ Computing number of distance attributes object """
        return len(self.get_distance())
    
    def set_distance_left(self, dis):
        """ Setting left distance artifically """
        self.distance_left = dis

    def set_distance_mid(self, dis):
        """ Setting middle distance artifically """
        self.distance_mid = dis

    def set_distance_right(self, dis):
        """ Setting right distance artifically """
        self.distance_right = dis


def convert_image_to_numpy_ndarray(imageframe_byte):
    """
    Convert sensors image data which is byte storage type to numpy array type
    
    Args:
        imageframe_byte: the byte type image data, 
            a member variable in ImagePackage class which defines in ADCPlatform
    Return:
        numpy array type image data
    """
    
    return numpy.array(Image.open(imageframe_byte))


def run(perceptionFlag, data, PerceptionArgs, distanceData, MyCar):
    """
    main function of perception module
    
    According to the data loaded from sensors (camera mainly) and some hyperparameters,
    the function runs the object detection algorithm and then estimate 
    distance of autonomous drving vehicle and three vehicles in front of it.
    
    Args:
        perceptionFlag: a flag that whether perception module is open in running
        data: sensors data, 
            a dict of 4 elements, including "control", "landLine", "radar" and "image" elements
        PerceptionArgs: object detection model and some args related to it, 
            a dict of 2 elements, including "predictor" and "args" elements
        MyCar: some hyperparameters of autonomous drving vechicle which initilize in initial.py,
            a object instantiated from the CarState class
    
    Return:
        None element
    """
    
    if not perceptionFlag:
        return None
    
    # multi threads confliction, time delayed 0.3 second
    time.sleep(0.3)
    
    while True:
        try:
            img = convert_image_to_numpy_ndarray(data["image"].byte)
            
            # Running object detection model and ditance estimation 
            results = detection.driving_runtime(predictor=PerceptionArgs["predictor"], 
                                                image=img, 
                                                args=PerceptionArgs["args"], 
                                                MyCar=MyCar)
            result_left  = results[0] 
            result_mid   = results[1]
            result_right = results[2]
            
            # When autonomous driving vehicle is running in the left lane, 
            # the left distance will be set to infinity to simplify lane change decision.
            if MyCar.midlane == MyCar.lanestate.LEFT:
                distanceData.set_distance_left(float('inf'))
            else:
                distanceData.set_distance_left(result_left.item())
            
            # When autonomous driving vehicle is running in the right lane,
            # the right distance will be set to infinyty to simplify lane change decision.
            if MyCar.midlane == MyCar.lanestate.RIGHT:
                distanceData.set_distance_right(float('inf'))
            else:
                distanceData.set_distance_right(result_right.item())
            
            # Setting middle distance all the time.
            distanceData.set_distance_mid(result_mid.item())
            
        except:
            # Function is running in a seperate thread, 
            # so no exception handling is required after an exception is caught.
            pass

    return None


