import ADCPlatform
import torch
import numpy
import math
from yolox.data.datasets import COCO_CLASSES
import tools.pid as pid
import perception.DrivingDetection as detection
import tools.lqr as lqr
import scipy.linalg as la


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
        self.superspeeduplimit = 101    # super speedup max speed
        self.superspeeduplimittime = 60 # super speedup time threshold
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

        self.LQR = lqr.State(x=0.0, y= 0.0, yaw=0.0, v=0.0)
        self.A = numpy.mat(numpy.zeros((4, 4)))
        self.B = numpy.mat(numpy.zeros((4, 1)))
        self.Q = numpy.eye(4)
        self.R = 1




    def dlqr(self, A, B, Q, R):
        def solve_DARE(A, B, Q, R):
            """
            solve a discrete time_Algebraic Riccati equation (DARE)
            """
            X = Q
            maxiter = 500
            eps = 0.01

            for i in range(maxiter):
                Xn = A.T * X * A - A.T * X * B * la.pinv(R + B.T * X * B) * B.T * X * A + Q
                if (abs(Xn - X)).max()  < eps:
                    X = Xn
                    break
                X = Xn

            return Xn
        # first, try to solve the ricatti equation
        X = solve_DARE(A, B, Q, R)

        # compute the LQR gain
        K = la.pinv(B.T * X * B + R) * (B.T * X * A)

        return K


    def initLQR(self):
        self.A[0, 0] = 1.0
        self.A[0, 1] = 0.1
        self.A[1, 2] = 0
        self.A[2, 2] = 1.0
        self.A[2, 3] = 0.1

        self.B[3, 0] = 0

        # TODO:change here
        self.Q[0,0] = 1.0
        self.Q[1,1] = 0
        self.Q[2,2] = 2.0
        self.Q[3,3] = 0

        self.R = 1

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

    

    


