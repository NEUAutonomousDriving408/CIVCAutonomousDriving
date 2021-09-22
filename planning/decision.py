from planning.findpath import findpath
# from perception.perception import DistanceData

'''xld - planning
stage 1 : speedup 加速到与前车保持10米距离 60km/h  45km/h
stage 2 : keeplane 保持稳定40km/h车速
stage 3 : changelane 变道

# 一开始都不满足 都不执行 仍然一直加速 直到stage1满足
# 当速度减小到40的时候stage2满足 求解出当前怎样变道 并切换overtake状态直到变道完成置位follow
# 如果与前车距离过远 加速一下 stage1等待满足
# * 此处没有overtake的状态机 主要在control中完成 overttake结束后自动切换至follow
'''

def run(distanceData, MyCar):
    distance_left, distance_mid, distance_right = distanceData.get_distance() 
    distance = [distance_left, distance_mid, distance_right]

    # stage 1
    # 读取sensor 正前方车辆距离数据 如果距离达到安全距离即可跟车
    if(distance_mid < MyCar.saftydistance and MyCar.cardecision == 'speedup'):  # 小于10米开始减速
        MyCar.cardecision = 'follow'  # stage0 -> stage1 更改状态之后distance < 10，等到车速降到400即可进行overtake
        return

    # stage 2
    # find target lane
    if(MyCar.cardecision == 'follow'
            and distance_mid < MyCar.saftydistance
            and not MyCar.changing  # 保证超车只判断一次即可
            and MyCar.speed < 43):  # follow 已将车速降下来

        # 超车完成后会自动回复到follow状态
        MyCar.cardecision = 'overtake'
        findpath(distance, MyCar)  # left or right
        return

    # stage 2-1
    # 对于变道时左侧车卡位的情况 而且当前处于speedup阶段需要快速变道
    # overtakesum 计数作弊
    if(MyCar.cardecision == 'speedup'
            and distance_mid > MyCar.saftydistance  # 远大于follow 12m条件
            and distance_left < 11  # 左侧车与前车很近
            and MyCar.midlane == -7   # 当前在最右车道
            and distance_mid - distance_left < 15
            # and not MyCar.changing  # 保证超车只判断一次即可
            # and MyCar.overtakeSum == 9
            ):  #

        # 超车完成后会自动回复到follow状态
        MyCar.cardecision = 'overtake'
        # findpath(distance, MyCar)  # left or right
        MyCar.direction = 'left'
        return

    # stage 2-2
    # 对于变道时左侧车卡位的情况 而且当前处于speedup阶段需要快速变道
    # overtakesum 计数作弊
    if(MyCar.cardecision == 'speedup'
            and distance_mid > MyCar.saftydistance  # 远大于follow 12m条件
            and distance_right < 11  # 左侧车与前车很近
            and MyCar.midlane == 7   # 当前在最右车道
            and distance_mid - distance_right < 15
            # and not MyCar.changing  # 保证超车只判断一次即可
            # and MyCar.overtakeSum == 9
            ):  #

        # 超车完成后会自动回复到follow状态
        MyCar.cardecision = 'overtake'
        # findpath(distance, MyCar)  # left or right
        MyCar.direction = 'right'
        return

    # stage 3
    # speedup and get close to the front car
    if (MyCar.cardecision == 'follow'
            and distance_mid > MyCar.saftydistance):
        MyCar.cardecision = 'speedup'
        return

