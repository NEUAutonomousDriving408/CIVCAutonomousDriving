import requests

# 设置的代理
__proxy = None
# 设置的Cookies
__cookies = None
# 设置请求头
__APNToken = None

# requests.packages.urllib3.disable_warnings()


# post请求
def __post(url, json_data):
    return requests.post(url, None, json_data, proxies=__proxy, cookies=__cookies)


# get请求带cookies
def __get(url, params):
    return requests.get(url, params, proxies=__proxy, cookies=__cookies)


# post请求返回json
def __post_with_json(url, json_data):
    return requests.post(url, None, json_data, proxies=__proxy, cookies=__cookies).json()


# get请求返回json
def __get_with_json(url, params):
    return requests.get(url, params, proxies=__proxy, cookies=__cookies).json()


# get请求带token
def __get_token(url, params):
    __headers = {
        'token': __APNToken
    }
    return requests.get(url, params, proxies=__proxy, headers=__headers)