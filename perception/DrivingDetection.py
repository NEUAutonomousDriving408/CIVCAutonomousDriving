#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author : HuangXinghui

import sys
sys.path.append("../")
from perception.isInTriangle import Vector2d, Triangle
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


"""
hyper parameters of single camera distance estimation
dimension : millimeter (mm)
"""
IMAGE_WIDTH = 480
IMAGE_HEIGHT = 360
CAMERA_FOCAL_LENGTH = 35
CAMERA_PIXEL_LENGTH = 0.1738
VEHICLE_LENGTH = 4780
VEHICLE_WIDTH = 2230
VEHICLE_HEIGHT = 1650


def distance_estimation(x0, y0, x1, y1, args):
    """
    Monocular camera ranging according to object detection.
    
    Calculate the distance using width and height seperately,
    and finally taking the average of the two estimates.
    
    Args:
        x0: top left corner x coordinate, float type
        y0: top left corner y coordinate, float type
        x1: bottom right corner x coordinate, float type
        y1: bottom right corner y coordinate, float type
        args: object detection model args, argparse type
    
    Return:
        estimation distance, dimension is meter
    """
    
    temp0 = VEHICLE_WIDTH * CAMERA_FOCAL_LENGTH
    temp1 = CAMERA_PIXEL_LENGTH * (x1 - x0) / (args.tsize / IMAGE_WIDTH)
    width_distance = temp0 / temp1
    
    temp2 = VEHICLE_HEIGHT * CAMERA_FOCAL_LENGTH
    temp3 = CAMERA_PIXEL_LENGTH * (y1 - y0) / (args.tsize / IMAGE_WIDTH)
    height_distance = temp2 / temp3
    
    average_distance = (width_distance + height_distance) / 2
    
    return average_distance / 1000


def visulize_after_processing(predictor, outputs, img_info, MyCar):
    """
    Mark out bounding boxes from object detection,
    and draw three triangle area.
    
    Args:
        predictor: the YOLOX detection model to inference, 
            including model and data postprocessing, 
            Predictor class type defined above
        outputs: the outputs of YOLOX model, torch.tensor type
        img_info: some image information defined in Predictor class, dict type
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py          
    """          
    # visulize the bounding box into the original image            
    result_image = predictor.visual(outputs[0], img_info, predictor.confthre)
    img = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)

    # left and right bound visulization
    # cv2.line(img, (227, 100), (227, 300), (0,0,0), 1, 4)
    # cv2.line(img, (252, 100), (252, 300), (0,0,0), 1, 4)

    # mid triangle visulization
    cv2.line(img, 
             (MyCar.triangle_mid.pointA_.x_, MyCar.triangle_mid.pointA_.y_), 
             (MyCar.triangle_mid.pointB_.x_, MyCar.triangle_mid.pointB_.y_), 
             (0,0,0), 1, 4)
    cv2.line(img, 
             (MyCar.triangle_mid.pointA_.x_, MyCar.triangle_mid.pointA_.y_), 
             (MyCar.triangle_mid.pointC_.x_, MyCar.triangle_mid.pointC_.y_), 
             (0,0,0), 1, 4)
    cv2.line(img, 
             (MyCar.triangle_mid.pointB_.x_, MyCar.triangle_mid.pointB_.y_), 
             (MyCar.triangle_mid.pointC_.x_, MyCar.triangle_mid.pointC_.y_), 
             (0,0,0), 1, 4)

    # left and right triangle visulization
    cv2.line(img, 
             (MyCar.triangle_left.pointA_.x_, MyCar.triangle_left.pointA_.y_), 
             (MyCar.triangle_left.pointC_.x_, MyCar.triangle_left.pointC_.y_), 
             (0,0,0), 1, 4)
    cv2.line(img, 
             (MyCar.triangle_left.pointC_.x_, MyCar.triangle_left.pointC_.y_), 
             (MyCar.triangle_left.pointB_.x_, MyCar.triangle_left.pointB_.y_), 
             (0,0,0), 1, 4)
    cv2.line(img, 
             (MyCar.triangle_right.pointA_.x_, MyCar.triangle_right.pointA_.y_),
             (MyCar.triangle_right.pointB_.x_, MyCar.triangle_right.pointB_.y_), 
             (0,0,0), 1, 4)
    cv2.line(img, 
             (MyCar.triangle_right.pointB_.x_, MyCar.triangle_right.pointB_.y_), 
             (MyCar.triangle_right.pointC_.x_, MyCar.triangle_right.pointC_.y_), 
             (0,0,0), 1, 4)

    # image showing
    cv2.imshow("AfterProcessing", img)
    cv2.waitKey(1)
    return


def make_parser(perceptionModel, left_num, right_num):
    """
    Initilizing argparse of YOLOX object detection model.
    Some detection hyperparameters is defined in this function.
    
    left_num and right_num parameters was used in the start version,
    and is already unused in the final version.
    
    Args:
        perceptionModel: yolox model name, a string defined in main.py
        left_num: left line bound of middle lane, int type
        right_num: right line bound of middle lane, int type
        
    Return:
        the yolox model args
    """
    parser = argparse.ArgumentParser("YOLOX Demo!")

    parser.add_argument("-lb", "--leftbound", type=int, default=left_num)
    parser.add_argument("-rb", "--rightbound", type=int, default=right_num)
    parser.add_argument("-expn", "--experiment-name", type=str, default=None)
    parser.add_argument("-n", "--name", type=str, default=perceptionModel, help="model name")

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
        default="./perception/YOLOX/exps/default/{}.py".format(perceptionModel),
        type=str,
        help="pls input your experiment description file",
    )
    parser.add_argument(
        "-c", 
        "--ckpt", 
        default="./perception/pretrainedmodel/{}.pth".format(perceptionModel), 
        type=str, 
        help="ckpt for eval"
    )
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
    
    return parser


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
   

def driving_runtime(predictor, image, args, MyCar):
    """
    Object detection and distance estimation function in autonomous driving
    
    Includes deep learning model inference, vehicles bounding boxes finding,
    left, middle, right direction distance estimation and
    detection image visulization after processing.
    
    Args:
        predictor: the YOLOX detection model to inference, 
            including model and data postprocessing, 
            Predictor class type defined above
        image: the input image, numpy.array type
        args: object detection model args, argparse type
        MyCar: autonomous driving vehicle parameters, 
            CarState class type defined in initial.py
    
    Return:
        a tuple of estimation distance of left, middle and right
        in front of the autonomous driving vehicle
    
    """
    
    # detection model inference 
    outputs, img_info = predictor.inference(image)

    # initilization of left, mid and right detection distance 
    distance_left = torch.tensor(float('inf'))
    distance_mid = torch.tensor(float('inf'))
    distance_right = torch.tensor(float('inf'))

    # point defination, initilization is random(0 and 0)
    point = Vector2d(0, 0)
    
    """
    When detecting the bounding boxes, enter this branch.
    Judging the left, mid and right bounding boxes
    in order to estimate the distance between autonomous driving vehicle and front vehicles.
    """
    if outputs[0] is not None:
        # initialize the index of left and right boundig boxes
        # If index number is not -1, there are vehicles in front of the autonomous deving vehicle.
        left_index = -1      
        right_index = -1
        mid_index = -1

        # list1 stores the index of model outputs 
        # list2 stores the bounding box area corresponding the list1 index
        midlist1 = list()
        midlist2 = list()
        leftlist1 = list()
        leftlist2 = list()
        rightlist1 = list()
        rightlist2 = list()


        """
        traversal
        find a mid, a left and a right bounding box 
        which is the biggest one of int the triangle area each other.
        """
        for i in range(outputs[0].shape[0]): 
            # centroid x pixel of bounding box 
            # bottom y is the bottom y pixek of bounding box 
            centroidX = outputs[0][i][0] + (outputs[0][i][2] - outputs[0][i][0]) / 2
            bottomY = outputs[0][i][3]

            # judging the confidence greater model oututs (two numbers multipul)
            # and judging the output classfications
            # class numbers : 2(car), 5(bus), 6(train), 7(truck)
            if (outputs[0][i][4] * outputs[0][i][5] > predictor.confthre) and \
                (outputs[0][i][6] == 2 or \
                 outputs[0][i][6] == 5 or \
                 outputs[0][i][6] == 7):
                # point is the bounding box, 
                # x caculated by box left and right average and y caculated by the box bottom
                # 1.3333 is caculated by 640 / 480
                point.x_ = centroidX / (args.tsize / IMAGE_WIDTH)
                point.y_ = bottomY / (args.tsize / IMAGE_WIDTH)
                
                area = (outputs[0][i][2] - outputs[0][i][0]) * (outputs[0][i][3] - outputs[0][i][1])

                # middle bounding box selection and select a max area box to estimate the distance.
                if MyCar.triangle_mid.isInTriangle(point):
                    
                    midlist1.append(i)
                    midlist2.append(area)

                # when autonomous drving vehicle is in middle lane or in right lane,
                # there will be a left bounding box to estimate distance.
                if (MyCar.midlane == MyCar.lanestate.MID or\
                    MyCar.midlane == MyCar.lanestate.RIGHT) and \
                    MyCar.changing == False and \
                    MyCar.triangle_left.isInTriangle(point): 
                        
                    leftlist1.append(i)
                    leftlist2.append(area)

                # when autonomous driving vehicle is in middle lane or left lane,
                # there will be a right bounding box to estimate distance.
                if (MyCar.midlane == MyCar.lanestate.MID or \
                    MyCar.midlane == MyCar.lanestate.LEFT) and \
                    MyCar.changing == False and \
                    MyCar.triangle_right.isInTriangle(point):
                        
                    rightlist1.append(i)
                    rightlist2.append(area)

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
    
    # image post processing and showing
    visulize_after_processing(predictor, outputs, img_info, MyCar)         

    return distance_left, distance_mid, distance_right
