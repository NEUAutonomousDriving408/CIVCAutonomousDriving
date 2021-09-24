
def findpath(distance, MyCar):

    # 当前所在车道
    whichlanenow = MyCar.midlane

    # 如果当前在坐车道 overtake只能向右
    if whichlanenow == 7.5:
        MyCar.direction = 'right'
    elif whichlanenow == -7.5:
        # if distance[0] < distance[1]:
        #     MyCar.direction = 'mid'
        #     # MyCar.changing = True
        #     MyCar.cardecision = 'follow'
        # else:
        MyCar.direction = 'left'
    # 中间车道要对比两侧距离后作出决策
    else:
        MyCar.direction = 'left' if distance[0] > distance[2] else 'right'



