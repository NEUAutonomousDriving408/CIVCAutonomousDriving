#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (c) Megvii, Inc. and its affiliates.

import sys
sys.path.append("../")
from tools.isInTriangle import Vector2d, Triangle
import argparse
import os
import time
from loguru import logger

import cv2

import torch

from yolox.data.data_augment import ValTransform
from yolox.data.datasets import COCO_CLASSES
from yolox.exp import get_exp
from yolox.utils import fuse_model, get_model_info, postprocess, vis

IMAGE_EXT = [".jpg", ".jpeg", ".webp", ".bmp", ".png"]

# hyper parameters of single camera distance estimation
# mm
IMAGE_WIDTH = 480
IMAGE_HEIGHT = 360
CAMERA_FOCAL_LENGTH = 35
CAMERA_PIXEL_LENGTH = 0.1738
VEHICLE_LENGTH = 4780
VEHICLE_WIDTH = 2230
VEHICLE_HEIGHT = 1650

def distance_estimation(x0, y0, x1, y1, args):
    temp1 = (VEHICLE_WIDTH * CAMERA_FOCAL_LENGTH) / (CAMERA_PIXEL_LENGTH * (x1 - x0) / (args.tsize / IMAGE_WIDTH))
    temp2 = (VEHICLE_HEIGHT * CAMERA_FOCAL_LENGTH) / (CAMERA_PIXEL_LENGTH * (y1 - y0) / (args.tsize / IMAGE_WIDTH))
    return (temp1 + temp2) / 2000


def make_parser(perceptionModel, left_num, right_num):
    parser = argparse.ArgumentParser("YOLOX Demo!")
    # parser.add_argument(
    #     "demo", default="image", help="demo type, eg. image, video and webcam"
    # )
    parser.add_argument("-lb", "--leftbound", type=int, default=left_num)
    parser.add_argument("-rb", "--rightbound", type=int, default=right_num)
    parser.add_argument("-expn", "--experiment-name", type=str, default=None)
    parser.add_argument("-n", "--name", type=str, default=perceptionModel, help="model name")

    parser.add_argument(
        "--path", default="./assets/dog.jpg", help="path to images or video"
    )
    parser.add_argument("--camid", type=int, default=0, help="webcam demo camera id")
    parser.add_argument(
        "--save_result",
        action="store_true",
        default=False,
        help="whether to save the inference result of image/video",
    )

    # exp file
    parser.add_argument(
        "-f",
        "--exp_file",
        default="./YOLOX/exps/default/{}.py".format(perceptionModel),
        type=str,
        help="pls input your experiment description file",
    )
    parser.add_argument("-c", "--ckpt", default=".//YOLOX/pretrainedmodel/{}.pth".format(perceptionModel), type=str, help="ckpt for eval")
    parser.add_argument(
        "--device",
        default="gpu",
        type=str,
        help="device to run our model, can either be cpu or gpu",
    )
    parser.add_argument("--conf", default=0.25, type=float, help="test conf")
    parser.add_argument("--nms", default=0.45, type=float, help="test nms threshold")
    parser.add_argument("--tsize", default=640, type=int, help="test img size")
    parser.add_argument(
        "--fp16",
        dest="fp16",
        default=False,
        action="store_true",
        help="Adopting mix precision evaluating.",
    )
    parser.add_argument(
        "--legacy",
        dest="legacy",
        default=False,
        action="store_true",
        help="To be compatible with older versions",
    )
    parser.add_argument(
        "--fuse",
        dest="fuse",
        default=False,
        action="store_true",
        help="Fuse conv and bn for testing.",
    )
    parser.add_argument(
        "--trt",
        dest="trt",
        default=False,
        action="store_true",
        help="Using TensorRT model for testing.",
    )
    return parser


def get_image_list(path):
    image_names = []
    for maindir, subdir, file_name_list in os.walk(path):
        for filename in file_name_list:
            apath = os.path.join(maindir, filename)
            ext = os.path.splitext(apath)[1]
            if ext in IMAGE_EXT:
                image_names.append(apath)
    return image_names


class Predictor(object):
    def __init__(
        self,
        model,
        exp,
        cls_names=COCO_CLASSES,
        trt_file=None,
        decoder=None,
        device="cpu",
        fp16=False,
        legacy=False,
    ):
        self.model = model
        self.cls_names = cls_names
        self.decoder = decoder
        self.num_classes = exp.num_classes
        self.confthre = exp.test_conf
        self.nmsthre = exp.nmsthre
        self.test_size = exp.test_size
        self.device = device
        self.fp16 = fp16
        self.preproc = ValTransform(legacy=legacy)
        if trt_file is not None:
            from torch2trt import TRTModule

            model_trt = TRTModule()
            model_trt.load_state_dict(torch.load(trt_file))

            x = torch.ones(1, 3, exp.test_size[0], exp.test_size[1]).cuda()
            self.model(x)
            self.model = model_trt

    def inference(self, img):
        img_info = {"id": 0}
        if isinstance(img, str):
            img_info["file_name"] = os.path.basename(img)
            img = cv2.imread(img)
        else:
            img_info["file_name"] = None

        height, width = img.shape[:2]
        img_info["height"] = height
        img_info["width"] = width
        img_info["raw_img"] = img

        ratio = min(self.test_size[0] / img.shape[0], self.test_size[1] / img.shape[1])
        img_info["ratio"] = ratio

        img, _ = self.preproc(img, None, self.test_size)
        img = torch.from_numpy(img).unsqueeze(0)
        img = img.float()
        if self.device == "gpu":
            img = img.cuda()
            if self.fp16:
                img = img.half()  # to FP16

        with torch.no_grad():
            t0 = time.time()
            outputs = self.model(img)
            if self.decoder is not None:
                outputs = self.decoder(outputs, dtype=outputs.type())
            outputs = postprocess(
                outputs, self.num_classes, self.confthre,
                self.nmsthre, class_agnostic=True
            )
            # logger.info("Infer time: {:.4f}s".format(time.time() - t0))
        return outputs, img_info

    def visual(self, output, img_info, cls_conf=0.35):
        ratio = img_info["ratio"]
        img = img_info["raw_img"]
        if output is None:
            return img
        output = output.cpu()

        bboxes = output[:, 0:4]

        # preprocessing: resize
        bboxes /= ratio

        cls = output[:, 6]
        scores = output[:, 4] * output[:, 5]

        vis_res = vis(img, bboxes, scores, cls, cls_conf, self.cls_names)
        return vis_res
   

def driving_runtime(predictor, vis_folder, image, args, MyCar):
    # detection model inference 
    outputs, img_info = predictor.inference(image)

    # initilization of left, mid and right detection distance 
    distance_left = torch.tensor(float('inf'))
    distance_mid = torch.tensor(float('inf'))
    distance_right = torch.tensor(float('inf'))

    # mid, left and right triangle defination
    triangle = Triangle()       # mid
    triangle_left = Triangle()  # left
    triangle_right = Triangle() # right

    triangle.pointA_.x_ = 240
    triangle.pointA_.y_ = 175
    triangle.pointB_.x_ = 160
    triangle.pointB_.y_ = 250
    triangle.pointC_.x_ = 320
    triangle.pointC_.y_ = 250

    triangle_left.pointA_.x_ = 240
    triangle_left.pointA_.y_ = 175
    triangle_left.pointB_.x_ = 160
    triangle_left.pointB_.y_ = 250
    triangle_left.pointC_.x_ = -70
    triangle_left.pointC_.y_ = 280

    triangle_right.pointA_.x_ = 240
    triangle_right.pointA_.y_ = 175
    triangle_right.pointB_.x_ = 550
    triangle_right.pointB_.y_ = 280
    triangle_right.pointC_.x_ = 320
    triangle_right.pointC_.y_ = 250

    # point defination, initilization is random(5 and 5.5)
    point = Vector2d()
    point.x_ = 5
    point.y_ = 5.5
    
    """
    When detecting the bounding boxes, enter this branch.
    Judging the left, mid and right bounding boxes
    in order to estimate the distance between autonomous driving vehicle and front vehicles.
    """
    if outputs[0] is not None:
        # initialize the index of left and right boundig boxes
        # if index number is not -1, there are vehicles in front of the autonomous deving vehicle.
        left_index = -1      
        right_index = -1
        mid_index = -1

        # list1 store the index of model outputs 
        # list2 store the bounding box area corresponding the list1 index
        leftlist1 = list()
        leftlist2 = list()
        rightlist1 = list()
        rightlist2 = list()
        midlist1 = list()
        midlist2 = list()

        """
        traversal
        find a mid, a left and a right bounding box 
        which is the biggest one of int the triangle area each other.
        """
        for i in range(outputs[0].shape[0]): 
            # centroid x pixel of bounding box 
            # bottom y this is the bottom bounding box  
            centroidX = outputs[0][i][0] + (outputs[0][i][2] - outputs[0][i][0]) / 2
            bottomY = outputs[0][i][3]

            # judging the confidence greater model oututs (two numbers multipul)
            # and judging the output classfications
            # class numbers : 2(car), 5 (bus), 6(train), 7(truck)
            if outputs[0][i][4] * outputs[0][i][5] > predictor.confthre and \
                (outputs[0][i][6] == 2 or outputs[0][i][6] == 5 or outputs[0][i][6] == 7):
                # point is the bounding box, 
                # x caculated by box left and right average and y caculated by the box bottom
                # 1.3333 is caculated by 640 / 480
                point.x_ = (outputs[0][i][0] + (outputs[0][i][2] - outputs[0][i][0]) / 2) / 1.33333
                point.y_ = outputs[0][i][3] / 1.33333

                # middle bounding box selection and select a max area box to estimate the distance.
                if triangle.isInTriangle(point):
                    midlist1.append(i)
                    midlist2.append( (outputs[0][i][2] - outputs[0][i][0]) * (outputs[0][i][3] - outputs[0][i][1]) )

                # when autonomous drving vehicle is in middle lane or in right lane,
                # there will be a left bounding box to estimate distance.
                if (MyCar.midlane == 0 or MyCar.midlane == MyCar.lanestate.RIGHT) and \
                    MyCar.changing == False and \
                    triangle_left.isInTriangle(point): 
                    leftlist1.append(i)
                    leftlist2.append( (outputs[0][i][2] - outputs[0][i][0]) * (outputs[0][i][3] - outputs[0][i][1]) )

                # when autonomous driving vehicle is in middle lane or left lane,
                # there will be a right bounding box to estimate distance.
                if (MyCar.midlane == 0 or MyCar.midlane == MyCar.lanestate.LEFT) and \
                    MyCar.changing == False and \
                    triangle_right.isInTriangle(point):
                    rightlist1.append(i)
                    rightlist2.append( (outputs[0][i][2] - outputs[0][i][0]) * (outputs[0][i][3] - outputs[0][i][1]) )

        # pick up a index of detection model outputs
        if midlist2:
            max_value_mid = max(midlist2)
            max_mid_index = midlist2.index(max_value_mid)
            mid_index = midlist1[max_mid_index]
        if leftlist2:
            maxvalue_left = max(leftlist2)
            max_left_index = leftlist2.index(maxvalue_left)
            left_index = leftlist1[max_left_index]
        if rightlist2:
            maxvalue_right = max(rightlist2)
            max_right_index = rightlist2.index(maxvalue_right)
            right_index = rightlist1[max_right_index]
        
        """
        Judging index of distance estimation index existing
        if index is existing, then calculate the distance of
        left and right lane opposite to the current vehicle.
        """
        if mid_index != -1:
            distance_mid = distance_estimation(outputs[0][mid_index][0].cpu().clone(), 
                                                        outputs[0][mid_index][1].cpu().clone(), 
                                                        outputs[0][mid_index][2].cpu().clone(), 
                                                        outputs[0][mid_index][3].cpu().clone(), 
                                                        args)
        if left_index != -1:
            distance_left = distance_estimation(outputs[0][left_index][0].cpu().clone(), 
                                                        outputs[0][left_index][1].cpu().clone(), 
                                                        outputs[0][left_index][2].cpu().clone(), 
                                                        outputs[0][left_index][3].cpu().clone(), 
                                                        args)
        if  right_index != -1:
            distance_right = distance_estimation(outputs[0][right_index][0].cpu().clone(), 
                                                        outputs[0][right_index][1].cpu().clone(), 
                                                        outputs[0][right_index][2].cpu().clone(), 
                                                        outputs[0][right_index][3].cpu().clone(), 
                                                        args)
  
    """
    image post processing and showing
    """          
    # visulize the bounding box into the original image            
    result_image = predictor.visual(outputs[0], img_info, predictor.confthre)
    img = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)

    # left and right bound visulization
    # cv2.line(img, (227, 100), (227, 300), (0,0,0), 1, 4)
    # cv2.line(img, (252, 100), (252, 300), (0,0,0), 1, 4)

    # mid triangle visulization
    cv2.line(img, (240, 175), (160, 250), (0,0,0), 1, 4)
    cv2.line(img, (240, 175), (320, 250), (0,0,0), 1, 4)
    cv2.line(img, (160, 250), (320, 250), (0,0,0), 1, 4)

    # left and right triangle visulization
    cv2.line(img, (240, 175), (-70, 280), (0,0,0), 1, 4)
    cv2.line(img, (-70, 280), (160, 250), (0,0,0), 1, 4)
    cv2.line(img, (240, 175), (550, 280), (0,0,0), 1, 4)
    cv2.line(img, (550, 280), (320, 250), (0,0,0), 1, 4)

    # image showing
    cv2.imshow("AfterProcessing", img)
    cv2.waitKey(1)

    return distance_left,  distance_mid, distance_right
