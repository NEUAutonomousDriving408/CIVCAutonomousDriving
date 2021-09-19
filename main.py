import ADCPlatform
import control
import planning.decision as planning
import initial.initial as initial
import sensor.loadsensor as sensor
import perception.perception as perception
from perception.perception import DistanceData
import threading

data = dict()
data["control"] = None
data["landLine"] = None
data["radar"] = None
data["image"] = None
result = None
# distance = {"data": float('inf')}
distanceData = DistanceData()

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

    result = ADCPlatform.start(serverUrl, username, password)

    if result:
        print("算法接入成功！")
        print("启动任务")
        ADCPlatform.start_task()
        
        # init func get sensor data
        SensorId, Controller, PerceptionArgs, MyCar = initial.init(perceptionFlag)

        # multi thread
        thread1 = threading.Thread(target=sensor.run, args=(SensorId, data, ))
        thread2 = threading.Thread(target=perception.run, args=(perceptionFlag, data, PerceptionArgs, distanceData, ))

        thread1.start()
        thread2.start()

        """
        这里加入感知图片返回数据主要改planning
        """
        previous_distance = float('inf')
        current_distance = float('inf')

        epoch = 1
        while True:
            print("current_distance: ", distanceData.get_distance())

            planning.run(distanceData.get_distance(), MyCar)
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
        thread1.join()
        thread2.join()

        ADCPlatform.stop()

    else:
        # 停止平台
        ADCPlatform.stop()
