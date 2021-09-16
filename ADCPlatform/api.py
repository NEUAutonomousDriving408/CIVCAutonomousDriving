from . import business
from .type_node import DataType, ImageType, SignBoard


# 开启
def start(url, username, password):
    business.__server_url = url
    result = business.__login(username, password)
    if result['RespCode'] == 6 and business.__get_task():
        return True
    else:
        stop()
        return False


# 关闭
def stop():
    business.__logout()


# 获取当前车辆安装传感器数据
def get_sensors():
    return business.__getSensors()


# 启动场景
def start_task():
    return business.__start_task()


# 获取图片
def get_image(sensorId):
    return business.__get_image(sensorId)

# 获取Data数据
def get_data(sensorId):
    return business.__get_data(sensorId)


# 第一题发送标志牌信息
def submit_sign_board(sign_board1: SignBoard, sign_board2: SignBoard, sign_board3: SignBoard):
    return business.__send_command('Sign', str(sign_board1.value + 1) + '/' + str(sign_board2.value + 1) + '/'
                                   + str(sign_board3.value + 1))


# 获取控制数据
def get_control_data():
    return business.__get_data(business.simtask['Sences']['Vehicles'][0]['ID'])


# 控制车辆
def control(throttle, steering, brake, gear):
    # business.__send_command('Throttle', '1')
    business.__send_command('control', str(throttle) + '/' + str(steering) + '/' + str(brake) + '/' + str(gear))


# 刹车
def brake(brake):
    # business.__send_command('Throttle', '1')
    business.__send_command('brake', str(brake))




