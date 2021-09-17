import ADCPlatform
import control


if __name__ == '__main__':
    # 开启平台SDK
    # 设置服务器访问地址
    serverUrl = 'https://web.simu.widc.icvrc.cn/api/'
    # 设置登录用户名
    username = 'YYX_zdjs'
    # 设置登录密码
    password = 'ps123456'
    result = ADCPlatform.start(serverUrl, username, password)
    if result:
        print("算法接入成功！")
        print("启动任务")
        ADCPlatform.start_task()

        # init func get sensor data
        # get sensor
        sensors = ADCPlatform.get_sensors()
        for sensor in sensors:
            if sensor.Name == "毫米波雷达":
                radarId = sensor.ID
            elif sensor.Name == "摄像机":
                cameraId = sensor.ID
            elif sensor.Name == "车道线传感器":
                landLineId = sensor.ID
            # print("名称：" + sensor.Name + ",ID:" + str(sensor.ID))


        # 启动算法接入任务控制车辆
        while True:
            # data = sensor()
            # result = perception(data)
            # decision = planning(result)
            control.run()
            # if(stop):
            #     break

        # 停止平台
        ADCPlatform.stop()

    else:
        # 停止平台
        ADCPlatform.stop()
