#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author : HuangXinghui Lordon

from initial.initial import CarState
from perception.perception import DistanceData


def run(distanceData, previous_distance, current_distance, MyCar):
    """
    Distance data smothing to better planning and control.
    
    Aiming at the unstable output of the deep learning model, 
    the data smoothing is designed, and the inf data is represented 
    by the distance of the previous successful recognition.
    
    Args:
        distanceData: Estimated distance data transmitted to the decision and control module,
            DistanceData class type defined in perception.py
        previous_distance: Last measured distance through model stability,
            DistanceData class type defined in perception.py
        current_distance: Current distance data from perception module,
            DistanceData class type defined in perception.py
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py
    
    Return: 
        None element
    """

    distance_left,  distance_mid, distance_right = distanceData.get_distance()

    
    # Setting middle distance
    if distance_mid != float('inf'):
        previous_distance.set_distance_mid(distance_mid)
    else:
        current_distance.set_distance_mid(previous_distance.distance_mid)
        distanceData.set_distance_mid(current_distance.distance_mid)
    
    if MyCar.changing:
        # When vehicle changes lane, all distance and previous distance set to infinity.
        distanceData.set_distance_left(float('inf'))
        distanceData.set_distance_right(float('inf'))
        distanceData.set_distance_mid(float('inf'))
        previous_distance.set_distance_left(float('inf'))
        previous_distance.set_distance_right(float('inf'))
        previous_distance.set_distance_mid(float('inf'))
    else:
        # Setting left and right distance
        if distance_left != float('inf'):
            previous_distance.set_distance_left(distance_left)
        else:
            current_distance.set_distance_left(previous_distance.distance_left)
            distanceData.set_distance_left(current_distance.distance_left)
        if distance_right != float('inf'):
            previous_distance.set_distance_right(distance_right)
        else:
            current_distance.set_distance_right(previous_distance.distance_right)
            distanceData.set_distance_right(current_distance.distance_right)
    
    # Judging overtake numbers and computing staight driving time.
    if MyCar.overtakeSum > MyCar.lastovertakeSum:
        MyCar.time = 0
        distanceData.set_distance_mid(float('inf'))
        distanceData.set_distance_left(float('inf'))
        distanceData.set_distance_right(float('inf'))
        MyCar.lastovertakeSum = MyCar.overtakeSum
    else:
        MyCar.time += 1
    
    return None


