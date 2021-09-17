import ADCPlatform
import control.pid as pid


class ControlData(object):
    def __init__(self):
        self.speed_kp = 1.20
        self.speed_ki = 0.02
        self.radarPid = pid.PID(self.speed_kp, self.speed_ki, 0)
        self.radarPidThread_1 = 6000
        self.radarPidThread_2 = 3000

        self.targetSpeedInit = 20.0 # 想要到达的速度
        self.speed_kd = 0.5
        self.speedPid = pid.PID(self.speed_kp, 0, self.speed_kp)
        self.speedPidThread_1 = 10
        self.speedPidThread_2 = 2

    
    def initPID(self):
        self.speedPid.clear()
        self.radarPid.clear()
        self.radarPid.setSetpoint(500.0)             # 跟车5m
        self.speedPid.setSetpoint(self.targetSpeedInit)              # 保持40km/h

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

    # control parameter initial
    Controller = ControlData()
    Controller.initPID()

    # if perceptionFlag is True, then initialize yolox model
    return SensorId, Controller

    

    


