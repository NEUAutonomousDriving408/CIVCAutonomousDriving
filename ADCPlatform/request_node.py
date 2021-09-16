import requests

# 存储node节点连接ip
__NodeAPN = None

# 设置的代理
__proxy = None

# 设置请求头
__APNToken = None
# 会话
__session = requests.Session()

requests.packages.urllib3.disable_warnings()


# get请求
def __get(url, params):
    __headers = {
        'APNToken': __APNToken
    }

    return __session.get(__NodeAPN + url, params=params, headers=__headers, verify=False)


# get请求返回json
def __get_with_json(url, params):
    __headers = {
        'APNToken': __APNToken
    }
    return __session.get(__NodeAPN + url, params=params, headers=__headers, verify=False).json()
