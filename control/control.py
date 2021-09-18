import ADCPlatform
import time
from PIL import Image
import numpy
import torch
import control.pid as pid
from yolox.data.datasets import COCO_CLASSES

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

''' xld - speed control
控制发送频率 100hz
'''
def run(Controller, MyCar, SensorID, direction):

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
    # 获取数据包
    landLine_package = ADCPlatform.get_data(SensorID["landLine"])
    try:
        positionnow = landLine_package.json[2]['A1'] + landLine_package.json[1]['A1']
    except AttributeError:
        pass
    if not control_data_package:
        print("任务结束")

    MyCar.speed = control_data_package.json['FS']
    MyCar.cao = control_data_package.json['CAO']

    # 纵向控制 thorro_ and brake_
    lontitudeControlSpeed(MyCar.speed, Controller.speedPid)

    # 横向控制 steer_
    if (MyCar.cardecision == 'changelane' and MyCar.speed < 41):
        if (direction == 'left'):
            Controller.latPid.setSetpoint(7 + MyCar.midlane)
        elif (direction == 'right'):
            Controller.latPid.setSetpoint(-7 + MyCar.midlane)
        latitudeControlpos(positionnow, Controller.latPid)
    else:
        latitudeControlpos(positionnow, Controller.latPid)

    ADCPlatform.control(Controller.speedPid.thorro_, Controller.latPid.steer_, Controller.speedPid.brake_, 1)
