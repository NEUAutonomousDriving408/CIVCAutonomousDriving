# from initial.initial import CarState
# from perception.perception import DistanceData

def findpath(distance, MyCar):

    # 当前所在车道
    whichlanenow = MyCar.midlane

    if whichlanenow == 7:
        MyCar.direction = 'right'
    elif whichlanenow == -7:
        # if distance[0] < distance[1]:
        #     MyCar.direction = 'mid'
        #     # MyCar.changing = True
        #     MyCar.cardecision = 'follow'
        # else:
        MyCar.direction = 'left'
    else:
        MyCar.direction = 'left' if distance[0] > distance[2] else 'right'



