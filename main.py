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
    image_left_bound = 303
    image_right_bound = 337

    result = ADCPlatform.start(serverUrl, username, password)

    if result:
        print("算法接入成功！")
        print("启动任务")
        ADCPlatform.start_task()
        
        # init func get sensor data
        SensorId, Controller, PerceptionArgs, MyCar = initial.init(perceptionFlag, image_left_bound, image_right_bound)

        # multi thread
        thread1 = threading.Thread(target=sensor.run, args=(SensorId, data, ))
        thread2 = threading.Thread(target=perception.run, args=(perceptionFlag, data, PerceptionArgs, distanceData, MyCar, ))

        thread1.start()
        thread2.start()

        """
        这里加入感知图片返回数据主要改planning
        """
        previous_distance_mid = float('inf')
        current_distance_mid = float('inf')
        previous_distance_left = float('inf')
        current_distance_left = float('inf')
        previous_distance_right = float('inf')
        current_distance_right = float('inf')

        epoch = 1
        while True:

            # data number processing
            distance_left,  distance_mid, distance_right = distanceData.get_distance()
            
            if distance_mid != float('inf'):
                previous_distance_mid = distance_mid
            else:
                current_distance_mid = previous_distance_mid
                distanceData.set_distance_mid(current_distance_mid)
            
            if MyCar.changing:
                distanceData.set_distance_left(float('inf'))
                distanceData.set_distance_right(float('inf'))
                previous_distance_left = float('inf')
                previous_distance_right = float('inf')
            else:
                if distance_left != float('inf'):
                    previous_distance_left = distance_left
                else:
                    current_distance_left = previous_distance_left
                    distanceData.set_distance_left(current_distance_left)
                if distance_right != float('inf'):
                    previous_distance_right = distance_right
                else:
                    current_distance_right = previous_distance_right
                    distanceData.set_distance_right(current_distance_right)
            print("current : ", distanceData.distance_mid, "left : ", distanceData.distance_left, "right : ", distanceData.distance_right)
            print("car decison : ", MyCar.cardecision)

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
        thread1.join()
        thread2.join()

        ADCPlatform.stop()

    else:
        # 停止平台
        ADCPlatform.stop()
