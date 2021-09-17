import ADCPlatform

data = dict()
data["control"] = None
data["landLine"] = None
data["radar"] = None
data["image"] = None

def run(SensorId):
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