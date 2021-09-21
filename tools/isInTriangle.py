
class Vector2d(object):
    def __init__(self):
        self.x_ = 0
        self.y_ = 0
    def CrossProduct(self, vector):
        return self.x_ * vector.y_ - self.y_ * vector.x_


    def Minus(self, vector):
        ans = Vector2d()
        ans.x_ = self.x_ - vector.x_
        ans.y_ = self.y_ - vector.y_
        return ans

class Triangle(object):
    def __init__(self):
        self.pointA_ = Vector2d()
        self.pointB_ = Vector2d()
        self.pointC_ = Vector2d()

    def isInTrangle(self, target):
        PA = self.pointA_.Minus(target)
        PB = self.pointB_.Minus(target)
        PC = self.pointC_.Minus(target)

        t1 = PA.CrossProduct(PB)
        t2 = PB.CrossProduct(PC)
        t3 = PC.CrossProduct(PA)

        return t1 * t2 >= 0 and t1 * t3 >= 0

def test():
    triangle = Triangle()
    triangle.pointA_.x_ = 240
    triangle.pointA_.y_ = 175

    triangle.pointB_.x_ = 160
    triangle.pointB_.y_ = 250

    triangle.pointC_.x_ = 320
    triangle.pointC_.y_ = 250

    point = Vector2d()
    point.x_ = 290
    point.y_ = 300

    print(triangle.isInTrangle(point))
