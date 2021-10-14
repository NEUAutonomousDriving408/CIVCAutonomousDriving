#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author : Lordon HuangXinghui

from planning.findpath import findpath
# from perception.perception import DistanceData


def run(distanceData, MyCar):
    '''
    stage 1 : speedup 加速到与前车保持safetydistance米距离
    stage 2 : keeplane 保持稳定40km/h车速
    stage 2-1 : coner case 变道时左侧车卡位，提前连环向左变道
    stage 2-2 : coner case 变道时右侧侧卡位，提前连环向右变道
    stage 3 : changelane 变道
    
    # speedup - follow - overtake 状态机版本（初始版）
    # 一开始都不满足 都不执行 仍然一直加速 直到stage1满足
    # 当速度减小到40的时候stage2满足 求解出当前怎样变道 并切换overtake状态直到变道完成置位follow
    # 如果与前车距离过远 加速一下 stage1等待满足
    # 此处没有overtake的状态机 主要在control中完成 overtake结束后自动切换至follow
    
    # speedup - overtake 状态机版本（当前版）
    # 一开始都不满足 都不执行 仍然一直加速 直到stage1满足
    # 检测到与前车的距离小于安全距离，切换到overtake
    # 此处没有overtake的状态机 主要在control中完成 overtake结束后自动切换至follow
    # 超过全部的车之后，向左一个车道行驶在中间车道，保证高速阶段不于道路两旁相撞
    
    Args:
        distanceData: Estimated distance data transmitted to the decision and control module,
            DistanceData class type defined in perception.py
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py
    '''
    distance_left, distance_mid, distance_right = distanceData.get_distance() 
    distance = [distance_left, distance_mid, distance_right]
    
    # 超过所有车后行驶在中间车道
    if MyCar.speed > 90 and MyCar.cardecision == 'speedup' and not MyCar.finalflag:
        MyCar.cardecision = 'overtake'
        MyCar.direction = 'left'
        MyCar.finalflag = True
        return

    # # 速度较小时安全距离也应该相应减小，防止与旁边后侧车道车辆相撞
    # if MyCar.speed < 45 and MyCar.cardecision == 'speedup':
    #     MyCar.saftydistance = 10
    #     # 高速时为15 相信速度控制
    # else:
    #     MyCar.saftydistance = 18

    # # stage 1
    # # 读取sensor 正前方车辆距离数据 如果距离达到安全距离即可跟车
    # # 小于safetydistance开始减速
    # if(distance_mid < MyCar.saftydistance and MyCar.cardecision == 'speedup'):  
    #     # stage0 -> stage1 更改状态之后distance < 10，等到车速降到40即可进行overtake
    #     MyCar.cardecision = 'follow'  
    #     return

    # stage 2
    # find target lane
    if(MyCar.cardecision == 'speedup'
            and distance_mid < MyCar.saftydistance # 13m
            and not MyCar.changing  # 保证超车只判断一次即可
            # and MyCar.speed < 43
            ):  # follow 已将车速降下来

        # 超车完成后会自动回复到follow状态
        MyCar.cardecision = 'overtake'
        findpath(distance, MyCar)  # left or right
        return

    # # stage 2-1
    # # 对于变道时左侧车卡位的情况 而且当前处于speedup阶段需要快速变道
    # if(MyCar.cardecision == 'speedup'
    #         and distance_mid > MyCar.saftydistance  # 远大于安全距离条件
    #         and distance_left < MyCar.saftydistance + 3 # 左侧车与前车很近
    #         and MyCar.midlane == MyCar.lanestate.RIGHT   # 当前在最右车道
    #         and distance_mid - distance_left < MyCar.saftydistance
    #         # and not MyCar.changing  # 保证超车只判断一次即可
    #         ):
    #     # 超车完成后会自动回复到follow状态
    #     MyCar.cardecision = 'overtake'
    #     # MyCar.midlane = 0
    #     # findpath(distance, MyCar)  # left or right
    #     MyCar.direction = 'left'
    #     return

    # # stage 2-2
    # # 对于变道时右侧车卡位的情况 而且当前处于speedup阶段需要快速变道
    # if(MyCar.cardecision == 'speedup'
    #         and distance_mid > MyCar.saftydistance  # 远大于安全距离条件
    #         and distance_right < MyCar.saftydistance + 3 # 左侧车与前车很近
    #         and MyCar.midlane == MyCar.lanestate.LEFT   # 当前在最左车道
    #         and distance_mid - distance_right < MyCar.saftydistance
    #         # and not MyCar.changing  # 保证超车只判断一次即可
    #         ):  
    #     # 超车完成后会自动回复到follow状态
    #     MyCar.cardecision = 'overtake'
    #     # MyCar.midlane = 0
    #     # findpath(distance, MyCar)  # left or right
    #     MyCar.direction = 'right'
    #     return

    # # stage 3
    # # speedup and get close to the front car
    # if (MyCar.cardecision == 'follow'
    #         and distance_mid > MyCar.saftydistance):
    #     MyCar.cardecision = 'speedup'
    #     return

