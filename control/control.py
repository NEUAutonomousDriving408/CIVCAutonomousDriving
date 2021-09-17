import ADCPlatform
import time
import control.pid as pid

# control param
speed_kp = 1.20
speed_ki = 0.02
radarPid = pid.PID(speed_kp, speed_ki, 0)
radarPidThread_1 = 6000
radarPidThread_2 = 3000

targetSpeedInit = 45.0 # 想要到达的速度
speed_kd = 0.5
speedPid = pid.PID(speed_kp, 0, speed_kp)
speedPidThread_1 = 10
speedPidThread_2 = 2

def init():
    speedPid.clear()
    radarPid.clear()

    radarPid.setSetpoint(500.0)             # 跟车5m
    speedPid.setSetpoint(targetSpeedInit)              # 保持40km/h

''' xld - speed pid control
加速时能够较快达到设定目标 
减速时能较快减到设定速度
stage 1 - 加速
stage 2 - 保持
stage 3 - 微调
stage 4 - 快速减速
stage 5 - 减速微调
'''
def lontitudeControlSpeed(speed, lonPid):
    lonPid.update(speed-5.0)
    if (lonPid.output > speedPidThread_1):# 加速阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 1')
        lonPid.thorro_ = 1
        lonPid.brake_ = 0
    elif (lonPid.output > speedPidThread_2):# 稳定控速阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 2')
        lonPid.thorro_ = min((lonPid.output / speedPidThread_1) * 0.85,1.0) #
        lonPid.brake_= min(((speedPidThread_1 - lonPid.output) / speedPidThread_1) * 0.1,1.0) #
    elif (lonPid.output > 0):# 下侧 微调
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 3')
        lonPid.thorro_ = (lonPid.output / speedPidThread_2) * 0.3#
        lonPid.brake_= ((speedPidThread_2 - lonPid.output) / speedPidThread_2) * 0.2
    elif (lonPid.output < -1 * speedPidThread_1):# 减速阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 4')
        lonPid.thorro_ = (-1 * lonPid.output / 5) * 0.2
        lonPid.brake_= 0.5
    else :
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 5')
        lonPid.thorro_ = (-1 * lonPid.output / speedPidThread_2) * 0.2
        lonPid.brake_= ((speedPidThread_2 - (-1 * lonPid.output)) / speedPidThread_2) * 0.4
    # print(lonPid.thorro_, '    ', lonPid.brake_)

# radar 障碍控制 与速度有关
def lontitudeControlRadar(value, lonPid):
    if(value): # for none type error
        lonPid.update(value)
        valuelast = value
    else:
        lonPid.update(lonPid.Setpoint)# 一般不会出现

    # pid to control
    if(lonPid.output >radarPidThread_1):# far away from front car
        lonPid.thorro_ =0.85
        lonPid.brake_ = 0
    elif(lonPid.output >radarPidThread_2):# brake softly
        lonPid.thorro_ = (lonPid.output / radarPidThread_1) * 0.65 #
        lonPid.brake_= ((radarPidThread_1 - lonPid.output) / radarPidThread_1) * 0.1 #
    else:
        lonPid.thorro_ = (lonPid.output / radarPidThread_2) * 0.3 #
        lonPid.brake_= ((radarPidThread_2 - lonPid.output) / radarPidThread_2) * 0.4 #


def run():
    # init control
    init()
    running = True
    # 毫米波真值传感器id
    radarId = 0
    # 摄像机传感器id
    cameraId = 0
    # 车道线传感器id
    landLineId = 0

    # get sensor
    sensors = ADCPlatform.get_sensors()
    for sensor in sensors:
        if sensor.Name == "毫米波雷达":
            radarId = sensor.ID
        elif sensor.Name == "摄像机":
            cameraId = sensor.ID
        elif sensor.Name == "车道线传感器":
            landLineId = sensor.ID
        # print("名称：" + sensor.Name + ",ID:" + str(sensor.ID))

    while running:
        # 获取车辆控制数据包
        control_data_package = ADCPlatform.get_control_data()
        if not control_data_package:
            print("任务结束")
            running = False
            break
        carSpeed = control_data_package.json['FS']
        # carX = control_data_package.json['X']
        # carY = control_data_package.json['Y']

        # 获取数据包 10101为雷达GPS等数据类型传感器id
        landLine_package = ADCPlatform.get_data(landLineId)
        data_package = ADCPlatform.get_data(radarId)# get rradar data to follow

        # 纵向障碍控制 speed pid update
        # radarValue = data_package.json[0]["Range"] * -1
        # lontitudeControlRadar(radarValue, radarPid)
        # 纵向速度控制 speed pid update
        lontitudeControlSpeed(carSpeed, speedPid)
        ADCPlatform.control(speedPid.thorro_, 0, speedPid.brake_, 1)

        # ADCPlatform.control(0.7, 0, 0,-1)
        # print("brake")

        # 休眠30毫秒
        # time.sleep(0.003)
