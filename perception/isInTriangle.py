#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author : Lordon

class Vector2d(object):
    def __init__(self, x=0, y=0):
        self.x_ = x
        self.y_ = y
    def CrossProduct(self, vector):
        return self.x_ * vector.y_ - self.y_ * vector.x_


    def Minus(self, vector):
        ans = Vector2d()
        ans.x_ = self.x_ - vector.x_
        ans.y_ = self.y_ - vector.y_
        return ans


class Triangle(object):
    def __init__(self, Ax=0, Ay=0, Bx=0, By=0, Cx=0, Cy=0):
        self.pointA_ = Vector2d(Ax, Ay)
        self.pointB_ = Vector2d(Bx, By)
        self.pointC_ = Vector2d(Cx, Cy)

    def isInTriangle(self, target):
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
