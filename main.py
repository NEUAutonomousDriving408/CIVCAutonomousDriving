import ADCPlatform
import control
import initial.initial as initial


if __name__ == '__main__':
    # 开启平台SDK
    # 设置服务器访问地址
    serverUrl = 'https://web.simu.widc.icvrc.cn/api/'
    # 设置登录用户名
    username = 'YYX_zdjs'
    # 设置登录密码
    password = 'ps123456'
    # whether initialize perception model
    perceptionFlag = False

    result = ADCPlatform.start(serverUrl, username, password)
    if result:
        print("算法接入成功！")
        print("启动任务")
        ADCPlatform.start_task()

        # init func get sensor data
        SensorId, Controller = initial.init(perceptionFlag)


        epoch = 1;
        change = True
        decisionSpeed = 60 # 速度控制
        while True: # start
            # data = sensor(SensorId)
            # result = perception(data)
            # decision = planning(result)
            control.run(Controller, decisionSpeed)
            # if(stop):
            #     break

            epoch += 1
            if (epoch == 1000):
                epoch = 1

        ADCPlatform.stop()

    else:
        # 停止平台
        ADCPlatform.stop()
