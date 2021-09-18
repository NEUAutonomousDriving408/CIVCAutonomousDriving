import findpath

'''xld - planning
stage 1 : speedup 加速到与前车保持10米距离 60km/h  45km/h
stage 2 : keeplane 保持稳定40km/h车速
stage 3 : changelane 变道
'''

state = 'speedup'
#
# def findTarget(data):
#     distance = 50
#     return distance
#
# def run(data, PerceptionArgs):
#
#     # go to control
#     if (state == 'changelane'):
#         # 结束之后置位 speedup
#         return 40, state
#
#
#
#     if (state == 'keeplane'):
#         # findpath 查找可行可行车道
#         # avaliableLane = findpath()
#         # state = 'changelane'
#
#         # changelane
#         # test 怎么变道 车身怎么改变的
#         # 左打 等一会儿 右打 都在control执行
#         return 40, state
#
#
#
#     # find target and lane keep and speed keep
#     distance = findTarget(data) # 当前车道到目标距离
#
#     # 车道保持
#     if 'speedup' == state and distance < 10 :
#         state = 'keeplane'
#         return 40, state # 车速保持
#
#     return speed, state