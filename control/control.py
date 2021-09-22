import ADCPlatform
import sys
sys.path.append("../")

speedPidThread_1 = 10  # 控制阈值1
speedPidThread_2 = 2  # 控制阈值2

''' xld - lat yr pid control
定速巡航下进行变道
yrsteer_ - pid计算方向盘输出 角速度补偿
'''
def latitudeyrControlpos(yr, yrPid):
    yrPid.update(yr)
    yrPid.yrsteer_ = yrPid.output * -1


''' xld - lat pid control
定速巡航下进行变道
positionnow = 车道多项式 A1之和
steer_ - pid计算方向盘输出
'''
def latitudeControlpos(positionnow, latPid):
    latPid.update(positionnow)
    latPid.steer_ = latPid.output * -1
    # 缓慢变道尝试 可以但没必要 不利于提速
    # if abs(latPid.steer_) > 70:
    #     latPid.steer_ = 70 if latPid.steer_ > 0 else -70

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
    if (lonPid.output > speedPidThread_1): # 加速阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 1')
        lonPid.thorro_ = 1
        lonPid.brake_ = 0
    elif (lonPid.output > speedPidThread_2):  # 稳定控速阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 2')
        lonPid.thorro_ = min((lonPid.output / speedPidThread_1) * 0.85, 1.0)
        lonPid.brake_ = min(((speedPidThread_1 - lonPid.output) / speedPidThread_1) * 0.1, 1.0)
    elif (lonPid.output > 0):  # 下侧 微调
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 3')
        lonPid.thorro_ = (lonPid.output / speedPidThread_2) * 0.3
        lonPid.brake_= ((speedPidThread_2 - lonPid.output) / speedPidThread_2) * 0.5
    elif (lonPid.output < -1 * speedPidThread_1):  # 减速阶段
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 4')
        lonPid.thorro_ = (-1 * lonPid.output / 5) * 0.3
        lonPid.brake_= 0.8
    else :
        # print('speed is:', speed, 'output is:', lonPid.output, 'stage 5')
        lonPid.thorro_ = (-1 * lonPid.output / speedPidThread_2) * 0.15
        lonPid.brake_ = abs((speedPidThread_2 - (-1 * lonPid.output)) / speedPidThread_2) * 0.6
        # lonPid.brake_ = 1.0
    print(lonPid.thorro_, '    ', lonPid.brake_)


def speedupJob(Controller, MyCar):
    Controller.speedPid.setSetpoint(Controller.speeduplimit)
    # 纵向控制 thorro_ and brake_
    lontitudeControlSpeed(MyCar.speed, Controller.speedPid)
    # 横向控制 steer_
    latitudeControlpos(MyCar.positionnow, Controller.latPid)
    ADCPlatform.control(Controller.speedPid.thorro_, Controller.latPid.steer_, Controller.speedPid.brake_, 1)

def followJob(Controller, MyCar):
    Controller.speedPid.setSetpoint(Controller.followlimit)
    # 纵向控制 thorro_ and brake_
    lontitudeControlSpeed(MyCar.speed, Controller.speedPid)
    # 横向控制 steer_
    latitudeControlpos(MyCar.positionnow, Controller.latPid)
    ADCPlatform.control(Controller.speedPid.thorro_, Controller.latPid.steer_, Controller.speedPid.brake_, 1)

def overtakeJob(Controller, MyCar):
    Controller.speedPid.setSetpoint(Controller.overtakelimit)
    # 纵向控制 thorro_ and brake_
    lontitudeControlSpeed(MyCar.speed, Controller.speedPid)

    # overtake 车道中线调整
    if (not MyCar.changing):
        if (MyCar.direction == 'left'):
            MyCar.midlane = min(7 , 7 + MyCar.midlane) # 最左侧不可左变道
        elif (MyCar.direction == 'right'):
            MyCar.midlane = max(-7 , -7 + MyCar.midlane)
        Controller.latPid.setSetpoint(MyCar.midlane)
        MyCar.changing = True # 更新中线 进入超车

    # overtake 切换 follow 状态跟车
    print("minus : ", MyCar.midlane - MyCar.positionnow)
    if (MyCar.changing and abs(MyCar.midlane - MyCar.positionnow) < 0.4):
        MyCar.cardecision = 'follow'
        MyCar.direction = 'mid'
        MyCar.changing = False
        MyCar.overtakeSum += 1

    # 横向控制 steer_ 加入角度速度约束
    latitudeyrControlpos(MyCar.yr, Controller.yrPid)
    # print('yr is', MyCar.yr, 'steeryr is', Controller.yrPid.yrsteer_) # overtake >15 , normal < 3
    # print('latsteer is ', Controller.latPid.steer_)
    latitudeControlpos(MyCar.positionnow, Controller.latPid)
    ADCPlatform.control(Controller.speedPid.thorro_,
                        Controller.latPid.steer_,  # - Controller.yrPid.yrsteer_,
                        Controller.speedPid.brake_, 1)

''' xld - speed control
'''
def run(Controller, MyCar, SensorID):

    # 获取车辆控制数据包
    control_data_package = ADCPlatform.get_control_data()
    # 获取数据包
    landLine_package = ADCPlatform.get_data(SensorID["landLine"])

    # 平台bug 存在读不到数据的情况
    if landLine_package:
        if landLine_package.json:
            if len(landLine_package.json) >= 3 and landLine_package.json[1] and landLine_package.json[2]:
                MyCar.positionnow = landLine_package.json[2]['A1'] + landLine_package.json[1]['A1']
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
        overtakeJob(Controller, MyCar)
    elif (MyCar.cardecision == 'speedup'):
        speedupJob(Controller, MyCar)
    elif (MyCar.cardecision == 'follow'):
        followJob(Controller, MyCar)

    # print(MyCar.cardecision, MyCar.midlane, MyCar.direction)
