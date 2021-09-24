import ADCPlatform
import control
import planning.decision as planning
import initial.initial as initial
import sensor.loadsensor as sensor
import perception.perception as perception
import perception.distanceprocessing as distanceprocessing
from perception.perception import DistanceData
import threading

data = dict()
data["control"] = None
data["landLine"] = None
data["radar"] = None
data["image"] = None
result = None
distanceData = DistanceData()
previous_distance =  DistanceData()
current_distance = DistanceData()

if __name__ == '__main__':
    # 开启平台SDK
    # 设置服务器访问地址
    serverUrl = 'https://web.simu.widc.icvrc.cn/api/'
    # 设置登录用户名
    username = 'YYX_zdjs'
    # 设置登录密码
    password = 'ps123456'
    # whether initialize perception model
    perceptionFlag = True
    image_left_bound = 303
    image_right_bound = 337

    result = ADCPlatform.start(serverUrl, username, password)

    if result:
        print("算法接入成功！")
        print("启动任务")
        ADCPlatform.start_task()
        
        # init func get sensor data
        SensorId, Controller, PerceptionArgs, MyCar = initial.init(perceptionFlag,
                                                                   image_left_bound,
                                                                   image_right_bound)
        # multi thread while true
        thread1 = threading.Thread(target=sensor.run, args=(SensorId, data, ))
        thread2 = threading.Thread(target=perception.run, args=(perceptionFlag,
                                                                data, PerceptionArgs,
                                                                distanceData, MyCar, ))
        thread1.start()
        thread2.start()

        epoch = 1
        while True:
            distanceprocessing.run(distanceData, previous_distance, current_distance, MyCar)
      
            print("current : ", distanceData.distance_mid, "left : ", distanceData.distance_left, "right : ", distanceData.distance_right)
            # print("car decison : ", MyCar.cardecision)

            planning.run(distanceData, MyCar)
            control.run(Controller, MyCar, SensorId)

            # if (MyCar.speed > 58):
            #     MyCar.cardecision = 'follow'
            # if (MyCar.cardecision == 'follow'
            #         and not MyCar.changing
            #         and MyCar.speed < 41):
            #     MyCar.cardecision = 'overtake'
            #     direction = 'right'

            epoch += 1
            if (epoch == 1000):
                epoch = 1

        # 到不了这里 能一直跑到平台关闭
        thread1.join()
        thread2.join()

        ADCPlatform.stop()

    else:
        # 停止平台
        ADCPlatform.stop()
