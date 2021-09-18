import ADCPlatform
# import time
# from PIL import Image
# import numpy
# import torch
# import control.pid as pid
# from yolox.data.datasets import COCO_CLASSES

import sys
sys.path.append("../")

import perception.DrivingDetection as detection

speedPidThread_1 = 10 # 控制阈值1
speedPidThread_2 = 2 # 控制阈值2


def latitudeControlpos(positionnow, latPid):
    latPid.update(positionnow)
    latPid.steer_ = latPid.output * -1


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
    elif (lonPid.output > speedPidThread_2): # 稳定控速阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 2')
        lonPid.thorro_ = min((lonPid.output / speedPidThread_1) * 0.85, 1.0)
        lonPid.brake_= min(((speedPidThread_1 - lonPid.output) / speedPidThread_1) * 0.1, 1.0)
    elif (lonPid.output > 0):# 下侧 微调
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 3')
        lonPid.thorro_ = (lonPid.output / speedPidThread_2) * 0.3
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


def changelanefun(side, MyCar):
    # steer -420 -- 420

    if (MyCar.speed - 40 > 2): # 稍等一会儿
        return 0

    if (abs(MyCar.cao) < 10.5 and MyCar.changelanestage == 0):
        MyCar.changelanestage = 1
    elif (abs(MyCar.cao) > 10.5 and MyCar.changelanestage == 1):
        MyCar.changelanestage = 2
    elif (abs(MyCar.cao) < 3 and MyCar.changelanestage == 2):
        MyCar.changelanestage = 3
    elif (abs(MyCar.cao) < 0.05 and MyCar.changelanestage == 3):
        MyCar.cardecision = 'keeplane'
        MyCar.changelanestage = 0

    # TODO:add position fineturn
    if(side == 'right' and MyCar.changelanestage == 1):
        return 40
    elif (side == 'right' and MyCar.changelanestage == 2):
        return -40
    elif(side == 'left' and MyCar.changelanestage == 1):
        return -40
    elif (side == 'left' and MyCar.changelanestage == 2):
        return 40
    elif (MyCar.changelanestage == 3):
        return 0

''' xld - speed control
控制发送频率 100hz
'''
def run(Controller, MyCar, SensorID):

    # 如果decision被planning进行了修改
    # 调整速度
    if (MyCar.cardecision == 'speedup'):
        Controller.speedPid.setSetpoint(60)
    elif (MyCar.cardecision == 'keeplane'):
        Controller.speedPid.setSetpoint(40)
    elif (MyCar.cardecision == 'changelane'):
        Controller.speedPid.setSetpoint(40)

    # 获取车辆控制数据包
    control_data_package = ADCPlatform.get_control_data()
    # 获取数据包 10101为雷达GPS等数据类型传感器id
    landLine_package = ADCPlatform.get_data(SensorID["landLine"])
    positionnow = landLine_package.json[2]['A1'] + landLine_package.json[1]['A1']
    if not control_data_package:
        print("任务结束")

    MyCar.speed = control_data_package.json['FS']
    MyCar.cao = control_data_package.json['CAO']

    # if (MyCar.cardecision == 'changelane'):
    #     steerout = changelanefun('left', MyCar)
    #     lontitudeControlSpeed(MyCar.speed, Controller.speedPid)
    #     ADCPlatform.control(Controller.speedPid.thorro_, steerout, Controller.speedPid.brake_, 1)
    #     return

    # 纵向控制 thorro_ and brake_
    lontitudeControlSpeed(MyCar.speed, Controller.speedPid)

    # 横向控制 steer_
    if (MyCar.cardecision == 'changelane' and MyCar.speed < 41):
        Controller.latPid.setSetpoint(6.8)
        latitudeControlpos(positionnow, Controller.latPid)
    else:
        latitudeControlpos(positionnow, Controller.latPid)

    ADCPlatform.control(Controller.speedPid.thorro_, Controller.latPid.steer_, Controller.speedPid.brake_, 1)
    # ADCPlatform.control(Controller.speedPid.thorro_, 0, Controller.speedPid.brake_, 1)
