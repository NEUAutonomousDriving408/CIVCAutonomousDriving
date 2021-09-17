import findpath

'''xld - planning
stage 1 : speedup 加速到与前车保持10米距离
stage 2 : keeplane 保持稳定40km/h车速
stage 3 : changlane 变道
'''
state = 'speedup'

def findTarget(data):
    distance = 50
    return distance

def run(data, PerceptionArgs):
    # find target and lane keep and speed keep

    distance = findTarget(data) # 当前车道到目标距离
    # 如果处于加速阶段
    if ('speedup' == state && distance < 15):
        state = 'keeplane'
        return 40 # 车速保持

    # find path







    return None