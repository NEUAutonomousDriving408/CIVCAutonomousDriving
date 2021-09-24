import ADCPlatform
import torch
from yolox.data.datasets import COCO_CLASSES
import tools.pid as pid
import perception.DrivingDetection as detection

class CarState(object):
    def __init__(self):
        self.speed = 0              # 车辆当前速度
        self.cao = 0                # 车辆当前姿态
        self.yr = 0                 # 车辆当前角速度
        self.cardecision = 'speedup'# planning计算得到决策
        self.midlane = 0            # 7 0 -7 latpid 参考 target
        self.positionnow = 0        # 两车道线A1求和
        self.changing = False       # 处于超车状态时为True
        # self.saftydistance = 11     # (最大时速50)与前车的安全距离 对于紧密跟车的情况 要准确识别并控速
        self.saftydistance = 14     # 与前车的安全距离 对于紧密跟车的情况 要准确识别并控速
        self.direction = 'mid'      # 当前行驶方向

        self.lastovertakeSum = 0
        self.overtakeSum = 0
        self.time = 0

class ControlData(object):
    def __init__(self):

        self.speeduplimit = 70
        self.followlimit = 40
        self.overtakelimit = 40

        self.lat_kp = 1.10
        self.lat_ki = 0.08
        self.lat_kd = 6.2
        self.latPid = pid.PID(self.lat_kp, self.lat_ki, self.lat_kd)

        self.yr_kp = 1.0
        self.yr_ki = 0.10
        self.yr_kd = 0
        self.yrPid = pid.PID(self.yr_kp, self.yr_ki, self.yr_kd)

        self.targetSpeedInit = 60.0 # 想要到达的速度
        self.speed_kp = 1.20
        self.speed_ki = 0.02
        self.speed_kd = 0.5
        self.speedPid = pid.PID(self.speed_kp, 0, self.speed_kp)
        self.speedPidThread_1 = 10
        self.speedPidThread_2 = 2

    def initPID(self):
        self.speedPid.clear() # lon
        self.latPid.clear()   # lat
        self.yrPid.clear()   # lat
        self.speedPid.setSetpoint(self.targetSpeedInit)              # 保持40km/h
        self.latPid.setSetpoint(0)             # lat aim 0
        self.yrPid.setSetpoint(0)             # lat aim 0

def init(perceptionFlag, image_left_bound, image_right_bound):
    # sensor initization

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

    # control parameter initialization
    Controller = ControlData()
    Controller.initPID()

    MyCar = CarState()

    # if perceptionFlag is True, then initialize yolox model
    # initialize network in perception
    predictor = None
    args = None
    if perceptionFlag:
        args = detection.make_parser(image_left_bound, image_right_bound).parse_args()
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

        if not args.trt:
            if args.ckpt is None:
                ckpt_file = os.path.join(file_name, "best_ckpt.pth")
            else:
                ckpt_file = args.ckpt
            # logger.info("loading checkpoint")
            ckpt = torch.load(ckpt_file, map_location="cpu")
            # load the model state dict
            model.load_state_dict(ckpt["model"])

        if args.trt:
            assert not args.fuse, "TensorRT model is not support model fusing!"
            trt_file = os.path.join(file_name, "model_trt.pth")
            assert os.path.exists(
                trt_file
            ), "TensorRT model is not found!\n Run python3 tools/trt.py first!"
            model.head.decode_in_inference = False
            decoder = model.head.decode_outputs
            logger.info("Using TensorRT to inference")
        else:
            trt_file = None
            decoder = None
        
        predictor = detection.Predictor(model, exp, COCO_CLASSES, trt_file, decoder, args.device, args.fp16, args.legacy)
        print("percetion model load.")
    
    PercetionArgs = dict()
    PercetionArgs["predictor"] = predictor
    PercetionArgs["args"] = args

    return SensorId, Controller, PercetionArgs, MyCar

    

    


