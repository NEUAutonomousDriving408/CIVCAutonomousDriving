# Author : Lordon

import ADCPlatform
import sys
sys.path.append("../")

"""
hyper parameters of single camera distance estimation
dimension : millimeter (mm)
"""
speedPidThread_1 = 10  # 控制阈值1
speedPidThread_2 = 2  # 控制阈值2

def latitudeyrControlpos(yr, yrPid):
    ''' 
    Lateral yr pid controller. use lateral angular velocity 
        to compensate lateral position control.

    Args:
        speed: car speed from ADCplatform.
        yrPid: lateral angular pid controller.
    
    Return: 
        None element
    '''
    yrPid.update(yr)
    yrPid.yrsteer_ = yrPid.output * -1


def latitudeControlpos(positionnow, latPid, MyCar):
    ''' 
    Lateral position pid controller to make the car 
        reach the target lane quickly and smoothly.

    Args:
        positionnow: car position now. 7 0 -7
        latPid: lateral position pid controller.
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py
    
    Return: 
        None element
    '''
    latPid.update(positionnow)
    latPid.steer_ = latPid.output * -1.0
    if MyCar.speed > 80:
        latPid.steer_ = latPid.output * -0.8
    # print("lattel : ", latPid.steer_)
    # 缓慢变道尝试 可以但没必要 不利于提速
    # if abs(latPid.steer_) > 200:
    #     latPid.steer_ = 200 if latPid.steer_ > 0 else -200


def lontitudeControlSpeed(speed, lonPid):
    ''' 
    Speed pid controller to make the car 
        reach the set speed quickly and brake.
        it includes five parts:
        stage 1 - speed
        stage 2 - keep speed
        stage 3 - finetune
        stage 4 - emergency brake
        stage 5 - brake finetune

    Args:
        speed: car speed from ADCplatform.
        lonPid: speed pid controller.
    
    Return: 
        None element
    '''
    lonPid.update(speed-5.0)
    if (lonPid.output > speedPidThread_1):    # 加速阶段
        # print('spezd is:', speed, 'output is:', lonPid.output, 'stage 1')
        lonPid.thorro_ = 1
        lonPid.brake_ = 0
    elif (lonPid.output > speedPidThread_2):  # 稳定控速阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 2')
        lonPid.thorro_ = min((lonPid.output / speedPidThread_1) * 0.85, 1.0)
        lonPid.brake_ = min(((speedPidThread_1 - lonPid.output) / speedPidThread_1) * 0.1, 1.0)
    elif (lonPid.output > 0):                 # 下侧 微调
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 3')
        lonPid.thorro_ = (lonPid.output / speedPidThread_2) * 0.3
        # 0.5会有稍减速的效果40-38 防碰撞
        lonPid.brake_= ((speedPidThread_2 - lonPid.output) / speedPidThread_2) * 0.5
    elif (lonPid.output < -1 * speedPidThread_1):  # 减速一阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 4')
        lonPid.thorro_ = (-1 * lonPid.output / 5) * 0.3
        # 减速第一阶段 仍然大于3m/s2 可选1.0 直接强制刹车
        lonPid.brake_= 1.0
    else :
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 5')
        lonPid.thorro_ = (-1 * lonPid.output / speedPidThread_2) * 0.15
        # 减速二阶段                 abs(2 - (2~10))/2 * 0.6
        # lonPid.brake_ = min(abs((speedPidThread_2 - (-1 * lonPid.output)) / speedPidThread_2) * 0.6, 1.0)
        lonPid.brake_ = 1.0
    # print(lonPid.thorro_, '    ', lonPid.brake_)


def speedupJob(Controller, MyCar):
    """
    Speedupjob is to finish speedup task.Send control 
    command to ADCPlatform.

    Args:
        Controller: controller params include speed and lat 
            pid controller.
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py
        distanceData: Estimated distance data transmitted to the decision and control module,
            DistanceData class type defined in perception.py
    
    Return: 
        None element
    """
    if MyCar.time >= Controller.superspeeduplimittime \
        and MyCar.overtakeSum != 0:
        Controller.speeduplimit = Controller.superspeeduplimit

    Controller.speedPid.setSetpoint(Controller.speeduplimit)
    # 纵向控制 thorro_ and brake_
    lontitudeControlSpeed(MyCar.speed, Controller.speedPid)
    # 横向控制 steer_
    latitudeControlpos(MyCar.positionnow, Controller.latPid, MyCar)
    ADCPlatform.control(Controller.speedPid.thorro_, Controller.latPid.steer_, Controller.speedPid.brake_, 1)


def followJob(Controller, MyCar):
    """
    Followjob is to finish follow task.Send control 
    command to ADCPlatform.

    Args:
        Controller: controller params include speed and lat 
            pid controller.
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py
        distanceData: Estimated distance data transmitted to the decision and control module,
            DistanceData class type defined in perception.py
    
    Return: 
        None element
    """
    Controller.speedPid.setSetpoint(Controller.followlimit)
    # 纵向控制 thorro_ and brake_
    lontitudeControlSpeed(MyCar.speed, Controller.speedPid)
    # 横向控制 steer_
    latitudeControlpos(MyCar.positionnow, Controller.latPid, MyCar)
    ADCPlatform.control(Controller.speedPid.thorro_, Controller.latPid.steer_, Controller.speedPid.brake_, 1)


def overtakeJob(Controller, MyCar, distanceData):
    """
    Overtakejob is to finish overtake task.Send control 
    command to ADCPlatform.

    Args:
        Controller: controller params include speed and lat 
            pid controller.
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py
        distanceData: Estimated distance data transmitted to the decision and control module,
            DistanceData class type defined in perception.py
    
    Return: 
        None element
    """
    Controller.speedPid.setSetpoint(Controller.overtakelimit)
    # 纵向控制 thorro_ and brake_
    lontitudeControlSpeed(MyCar.speed, Controller.speedPid)

    # overtake 车道中线调整
    if (not MyCar.changing):
        # 最左侧不可左变道
        if (MyCar.direction == 'left'):
            MyCar.midlane = min(MyCar.lanestate.LEFT , MyCar.lanestate.LEFT + MyCar.midlane)
        # 最右侧不可右变道
        elif (MyCar.direction == 'right'):
            MyCar.midlane = max(MyCar.lanestate.RIGHT , MyCar.lanestate.RIGHT + MyCar.midlane)
        Controller.latPid.setSetpoint(MyCar.midlane)
        # 更新中线state 进入超车
        MyCar.changing = True

    # overtake 完成 切换 follow 状态跟车
    # print("minus : ", MyCar.midlane - MyCar.positionnow)
    # if (MyCar.changing and abs(MyCar.midlane - MyCar.positionnow) < 0.5):
    if (MyCar.changing and 
        (distanceData.distance_mid > 20
        or abs(MyCar.midlane - MyCar.positionnow) < 0.5)
        ):
        MyCar.cardecision = 'speedup'
        MyCar.direction = 'mid'
        MyCar.changing = False
        MyCar.overtakeSum += 1

    # 横向控制 steer_ 加入角度速度约束
    latitudeyrControlpos(MyCar.yr, Controller.yrPid)
    # print('yr is', MyCar.yr, 'steeryr is', Controller.yrPid.yrsteer_) # overtake >15 , normal < 3
    # print('latsteer is ', Controller.latPid.steer_)
    latitudeControlpos(MyCar.positionnow, Controller.latPid, MyCar)
    ADCPlatform.control(Controller.speedPid.thorro_,
                        Controller.latPid.steer_ + 0.01 * Controller.yrPid.yrsteer_,
                        Controller.speedPid.brake_, 1)


def run(Controller, MyCar, SensorID, distanceData):
    """
    Control methord.
    
    Args:
        Controller: controller params include speed and lat 
            pid controller.
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py
        distanceData: Estimated distance data transmitted to the decision and control module,
            DistanceData class type defined in perception.py
    
    Return: 
        None element
    """

    # 获取车辆控制数据包
    control_data_package = ADCPlatform.get_control_data()
    # 获取数据包
    landLine_package = ADCPlatform.get_data(SensorID["landLine"])
    temp1 = 0.0
    temp2 = 0.0

    x1 = MyCar.lanefuture ** 0
    x2 = MyCar.lanefuture ** 1
    x3 = MyCar.lanefuture ** 2
    x4 = MyCar.lanefuture ** 3

    # 平台bug 存在读不到数据的情况
    if landLine_package:
        if landLine_package.json:
            # 取中间两车道数据
            if len(landLine_package.json) >= 3 and landLine_package.json[1] and landLine_package.json[2]:
                # MyCar.positionnow = landLine_package.json[2]['A1'] + landLine_package.json[1]['A1']
                # 拿到车道线反映出的车身位置
                temp1 = x1 * landLine_package.json[1]['A1'] + x2 * landLine_package.json[1]['A2'] + x3 * landLine_package.json[1]['A3'] + x4 * landLine_package.json[1]['A4']
                temp2 = x1 * landLine_package.json[2]['A1'] + x2 * landLine_package.json[2]['A2'] + x3 * landLine_package.json[2]['A3'] + x4 * landLine_package.json[2]['A4']
                MyCar.positionnow = temp1 + temp2
            else:
                pass
        else:
            pass
    else:
        pass

    if not control_data_package:
        print("任务结束")

    MyCar.speed = control_data_package.json['FS']
    MyCar.cao = control_data_package.json['CAO']
    MyCar.yr = control_data_package.json['YR']

    # 有限3种状态任务
    if (MyCar.cardecision == 'overtake'):
        overtakeJob(Controller, MyCar, distanceData)
    elif (MyCar.cardecision == 'speedup'):
        speedupJob(Controller, MyCar)
    elif (MyCar.cardecision == 'follow'):
        followJob(Controller, MyCar)

    # print(MyCar.cardecision, MyCar.midlane, MyCar.direction)
    # print("temp1+temp2 : ", temp1 + temp2)
