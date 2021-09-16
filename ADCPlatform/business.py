from . import request_basic
from . import request_node
from . import type_node
from io import BytesIO

# 存储服务器地址
__server_url = ''

# 协议头
__protocol = 'https://'

# 存储当前的TaskInfo信息
simtask = None


# 登录接口，返回登录信息
def __login(username, password):
    data = {"account": username,
            "password": password}
    result = request_basic.__post(__server_url + "/sys/Login", data)
    request_basic.__APNToken = result.json()['Data']['token']
    return result.json()


# 登出接口，Bool型返回值， 成功返回True，否则返回Flase
def __logout():
    request_basic.__get_with_json(__server_url + "/sys/LogOut", None)
    request_basic.__cookies = None
    request_basic.__APNToken = None


# 发送命令接口，Bool型返回值， 成功返回True，否则返回Flase
def __send_command(command, value):
    global simtask
    if not simtask:
        return False
    vehicle_id = simtask['Sences']['Vehicles'][0]['ID']
    result = request_node.__get("/Command/" + command + "/" + value, None)
    if result.status_code == 200:
        return True
    else:
        return False


# 获取当前正在执行的任务数据
def __get_task():
    result = request_basic.__get_token(__server_url + "Question/GetUserRunningSimTask", None)
    task = result.json()
    if task['RespCode'] == 1:
        # 设置当前任务Token
        request_node.__APNToken = task['Data']['Sences']['Token']
        # 设置当前任务APN
        request_node.__NodeAPN = __protocol + task['Data']['Sences']['APN'] + ":" + str(task['Data']['Sences']['HttpPort'])
        global simtask
        simtask = task['Data']
        return True
    else:
        return False


# 获取车辆安装传感器数据
def __getSensors():
    if not simtask:
        return None
    sensors = []
    for s in simtask['Sences']['Vehicles'][0]['Sensors']:
        sensor = type_node.SensorInfo(s['ID'],s['Name'])
        sensors.append(sensor)
    return sensors


# 发送开始测试指令
def __start_task():
    result = request_node.__get("/Command/start/1", None)
    if result.status_code == 200:
        return True
    return False


# 获取图片接口，返回ImagePackage
def __get_image(objectId):
    result = request_node.__get("/widc/data/" + str(objectId), None)
    if result==None or len(result.content) == 0:
        return None
    image_package = type_node.ImagePackage()
    image_package.timestamp = result.headers['TimeStamp']
    image_package.byte = BytesIO(result.content)
    return image_package


# 获取数据接口，返回DataPackage
def __get_data(objectId):
    result = request_node.__get("/widc/data/" + str(objectId), None)
    if result==None or len(result.content) == 0:
        return None
    data_package = type_node.DataPackage()
    data_package.timestamp = result.headers['TimeStamp']
    data_package.json = result.json()
    return data_package


# 错误处理接口
def __error(result):
    return result['respMsg']
