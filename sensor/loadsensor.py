#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author : HuangXinghui

import ADCPlatform

def run(SensorId, data):
    """
    main function of loading sensor data from simulation platform
    
    The function runs in a seperated thread so that data acquisition and 
    data processing are completed in parallel to reduce the instruction sending interval.
    
    Args:
        SensorId: sensors ID from platform to uniquely identify the vehicle sensor, 
            it is returned by initalial.init function, int type
        data: sensors data, 
            a dict of 4 elements, including "control", "landLine", "radar" and "image" elements
    
    Return:
        data, a incoming and outgoing parameter
    """

    while True:
        landLineId = SensorId["landLine"]
        # radarId = SensorId["radar"]
        cameraId = SensorId["camera"]

        # 获取数据包 10101为雷达GPS等数据类型传感器id
        # control_data_package = ADCPlatform.get_control_data()
        landLine_package = ADCPlatform.get_data(landLineId)
        # radar_package = ADCPlatform.get_data(radarId)
        image_package = ADCPlatform.get_image(cameraId)
        # print(image_package.timestamp)

        # data["control"] = control_data_package
        data["landLine"] = landLine_package
        # data["radar"] = radar_package
        data["image"] = image_package
    return data