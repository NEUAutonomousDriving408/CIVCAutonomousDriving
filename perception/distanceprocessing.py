# from initial.initial import CarState
# from perception.perception import DistanceData

def run(distanceData, previous_distance, current_distance, MyCar):

    distance_left,  distance_mid, distance_right = distanceData.get_distance()

    """
    distance data smothing to better planning and control
    """

    if distance_mid != float('inf'):
        previous_distance.set_distance_mid(distance_mid)
    else:
        current_distance.set_distance_mid(previous_distance.distance_mid)
        distanceData.set_distance_mid(current_distance.distance_mid)
    
    if MyCar.changing:
        distanceData.set_distance_left(float('inf'))
        distanceData.set_distance_right(float('inf'))
        distanceData.set_distance_mid(float('inf'))
        previous_distance.set_distance_left(float('inf'))
        previous_distance.set_distance_right(float('inf'))
        previous_distance.set_distance_mid(float('inf'))
    else:
        if distance_left != float('inf'):
            previous_distance.set_distance_left(distance_left)
        else:
            current_distance.set_distance_left(previous_distance.distance_left)
            distanceData.set_distance_left(current_distance.distance_left)
        if distance_right != float('inf'):
            previous_distance.set_distance_right(distance_right)
        else:
            current_distance.set_distance_right(previous_distance.distance_right)
            distanceData.set_distance_right(current_distance.distance_right)
    
    # TODO:distance judging bug
    if MyCar.overtakeSum > MyCar.lastovertakeSum:
        distanceData.set_distance_mid(float('inf'))
        distanceData.set_distance_left(float('inf'))
        distanceData.set_distance_right(float('inf'))
        MyCar.lastovertakeSum = MyCar.overtakeSum
    
    return


