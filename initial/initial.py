#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author : Lordon HuangXinghui

import os
import torch

import ADCPlatform
import perception.DrivingDetection as detection
import control.pid as pid
from perception.isInTriangle import Vector2d, Triangle
from yolox.data.datasets import COCO_CLASSES


class LaneState(object):
    """
    The lane state class using lateral control
    A target number of driving lane, which is the sum of two dashed lane line.
    
    Attributes:
        LEFT: left lane target, float type
        MID: middle lane target, float type
        RIGHT: right lane target, float type
    """
    
    def __init__(self, l=7.5, m=0.0, r=-7.5):
        """ Initializing three lane target number """
        self.LEFT = l
        self.MID = m
        self.RIGHT = r
    
    def set_leftlane(self, l):
        self.LEFT = l
    
    def set_midlane(self, m):
        self.MID = m
    
    def set_rightlane(self, r):
        self.RIGHT = r


class CarState(object):
    """
    车辆状态和车辆行驶算法相关的标志位与参数
    """
    
    def __init__(self):
        self.lanestate = LaneState(7, 0, -8) # 左中右车道线目标位置
        self.speed = 0                       # 车辆当前速度
        self.cao = 0                         # 车辆当前姿态
        self.yr = 0                          # 车辆当前角速度
        self.positionnow = 0                 # 两车道线A1求和
        
        self.cardecision = 'speedup'         # planning计算得到决策
        self.direction = 'mid'               # 当前行驶方向
        self.changing = False                # 处于超车状态时为True
        self.midlane = self.lanestate.MID    # 7.5 0 -8 latpid 参考 target
        self.lanefuture = 2.0                # 车道线 x = 2 处的位置
        self.saftydistance = 18              # 与前车的安全距离 对于紧密跟车的情况 要准确识别并控速
        self.lastovertakeSum = 0             # 超车计数与数据平滑辅助变量
        self.overtakeSum = 0                 # 超车计数
        self.time = 0                        # 超级加速阶段计时
        self.finalflag = False               # 超级加速阶段回到中间车道标志位
        
        # Initilize three triangles using perception
        self.triangle_mid = Triangle(240, 175, 160, 250, 320, 250)
        self.triangle_left = Triangle(240, 175, 160, 250, -70, 280)
        self.triangle_right = Triangle(250, 175, 550, 280, 320, 250)


class ControlData(object):
    """
    车辆控制算法相关参数
    """
    
    def __init__(self):

        self.speeduplimit = 85               # 加速阶段控制速度
        self.superspeeduplimit = 101         # 超级加速阶段控制速度
        self.superspeeduplimittime = 45      # 超级加速阶段计时阈值
        self.followlimit = 40                # 跟车阶段控制速度
        self.overtakelimit = 72              # 超车阶段控制速度
        
        # 横向控制PID参数
        self.lat_kp = 2.10
        self.lat_ki = 0.07
        self.lat_kd = 6.96
        self.latPid = pid.PID(self.lat_kp, self.lat_ki, self.lat_kd)
        
        # 方向角控制PID参数
        self.yr_kp = 1.0
        self.yr_ki = 0.10
        self.yr_kd = 0
        self.yrPid = pid.PID(self.yr_kp, self.yr_ki, self.yr_kd)
        
        # 纵向控制PID参数
        self.targetSpeedInit = 60.0          # 想要到达的速度
        self.speed_kp = 1.20
        self.speed_ki = 0.02
        self.speed_kd = 0.5
        self.speedPid = pid.PID(self.speed_kp, 0, self.speed_kp)
        self.speedPidThread_1 = 10
        self.speedPidThread_2 = 2

    def initPID(self):
        self.speedPid.clear() # lon
        self.latPid.clear()   # lat
        self.yrPid.clear()    # lat
        self.speedPid.setSetpoint(self.targetSpeedInit)  # 保持40km/h
        self.latPid.setSetpoint(0)             # lat aim 0
        self.yrPid.setSetpoint(0)              # lat aim 0


def init(perceptionFlag, perceptionModel, image_left_bound=0, image_right_bound=0):
    """
    main function of initilization
    Initilizing sensor ID, control data and perception model.
    
    Args:
        perceptionFlag: a flag that whether perception module is open in running
        PerceptionArgs: object detection model and some args related to it, 
            a dict of 2 elements, including "predictor" and "args" elements
        image_left_bound: left line bound of middle lane, int type
        image_right_bound: right line bound of middle lane, int type
    
    Return:
        SensorId: sensors ID from platform to uniquely identify the vehicle sensor, 
            it is returned by initalial.init function, int type
        Controller: control parameters, ControlData class type defined in initial.py
        PerceptionArgs: object detection model and some args related to it, 
            a dict of 2 elements, including "predictor" and "args" elements
        MyCar: autonomous driving vehicle states and parameters,
            CarState class type defined in initial.py
    """
    
    """
    sensor initization 
    """
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
    
    """
    control parameters initialization
    instantiation of ControlData and CarState
    """
    Controller = ControlData()
    Controller.initPID()

    MyCar = CarState()
    
    
    """
    perception parameters initilization
    if perceptionFlag is True, then initialize yolox model
    initialize network in perception
    """
    predictor = None
    args = None
    if perceptionFlag:

        if perceptionModel not in {"yolox_tiny", "yolox_s", "yolox_m", "yolox_l", "yolox_x"}:
            raise RuntimeError("detection model must be a yolox model!")

        args = detection.make_parser(perceptionModel, 
                                     image_left_bound, 
                                     image_right_bound).parse_args()
        exp = detection.get_exp(args.exp_file, args.name)
        if args.conf is not None:
            exp.test_conf = args.conf
        if args.nms is not None:
            exp.nmsthre = args.nms
        if args.tsize is not None:
            exp.test_size = (args.tsize, args.tsize)
        model = exp.get_model()
        if args.device == "gpu":
            model.cuda()
        if args.fp16:
            model.half()  # to FP16
        model.eval()

        if args.ckpt is None:
            raise RuntimeError("please input a pretrained model path in DrivingDetection.py")
        else:
            ckpt_file = args.ckpt
        ckpt = torch.load(ckpt_file, map_location="cpu")
        # load the model state dict
        model.load_state_dict(ckpt["model"])

        trt_file = None
        decoder = None
        
        predictor = detection.Predictor(model, exp, COCO_CLASSES, 
                                        trt_file, decoder, 
                                        args.device, args.fp16, args.legacy)
        print("perception model load.")
    else:
        print("no perception modol.")
    
    PerceptionArgs = dict()
    PerceptionArgs["predictor"] = predictor
    PerceptionArgs["args"] = args

    return SensorId, Controller, PerceptionArgs, MyCar

