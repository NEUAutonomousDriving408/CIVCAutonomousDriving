import ADCPlatform


def init(perceptionFlag):
    # get sensor

    # 毫米波真值传感器id
    radarId = 0
    # 摄像机传感器id
    cameraId = 0
    # 车道线传感器id
    landLineId = 0
    SensorId = dict()

    sensors = ADCPlatform.get_sensors()
    for sensor in sensors:
        if sensor.Name == "毫米波雷达":
            radarId = sensor.ID
        elif sensor.Name == "摄像机":
            cameraId = sensor.ID
        elif sensor.Name == "车道线传感器":
            landLineId = sensor.ID
        print("名称：" + sensor.Name + ",ID:" + str(sensor.ID))
    
    SensorId["radar"] = radarId
    SensorId["camera"] = cameraId
    SensorId["landLine"] = landLineId

    # if perceptionFlag is True, then initialize yolox model
    return SensorId

    

    


