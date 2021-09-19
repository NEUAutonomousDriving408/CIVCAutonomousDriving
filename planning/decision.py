import findpath

'''xld - planning
stage 1 : speedup 加速到与前车保持10米距离 60km/h  45km/h
stage 2 : keeplane 保持稳定40km/h车速
stage 3 : changelane 变道
'''


def findTarget(data):
    distance = 50
    return distance

def run(distance, MyCar):

    # stage 1
    # 读取sensor 正前方车辆距离数据
    if(distance < MyCar.saftydistance and MyCar.cardecision == 'speedup'): #小于10米开始减速
        MyCar.cardecision = 'follow' # stage0 -> stage1 更改状态之后distance < 10，等到车速降到400即可进行overtake
        return

    # stage 2
    # find target lane
    if(MyCar.cardecision == 'follow'
            and not MyCar.changing # 保证超车只判断一次即可
            and MyCar.speed < 41): # follow 已将车速降下来
        MyCar.cardecision = 'overtake'
        # findpath() # left or right
        MyCar.direction = 'right'
        # 超车完成后会自动回复到follow状态
        return

    # stage 3
    # speedup and get close to the front car
    if (MyCar.cardecision == 'follow'
            and distance > MyCar.saftydistance):
        MyCar.cardecision = 'speedup'
        return

    # 一开始都不满足 都不执行 仍然一直加速 直到stage1满足
    # 当速度减小到40的时候stage2满足 求解出当前怎样变道 并切换overtake状态直到变道完成置位follow
    # 如果与前车距离过远 加速一下 stage1等待满足
    # * 此处没有overtake的状态机 主要在control中完成 overttake结束后自动切换至follow
