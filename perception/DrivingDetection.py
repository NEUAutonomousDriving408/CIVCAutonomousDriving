#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (c) Megvii, Inc. and its affiliates.

import sys
sys.path.append("../")
import ADCPlatform
from initial.initial import CarState
import argparse
import os
import time
from loguru import logger

import cv2

import torch
import numpy as np

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


def make_parser(left_num, right_num):
    parser = argparse.ArgumentParser("YOLOX Demo!")
    # parser.add_argument(
    #     "demo", default="image", help="demo type, eg. image, video and webcam"
    # )
    parser.add_argument("-lb", "--leftbound", type=int, default=left_num)
    parser.add_argument("-rb", "--rightbound", type=int, default=right_num)
    parser.add_argument("-expn", "--experiment-name", type=str, default=None)
    parser.add_argument("-n", "--name", type=str, default="yolox-l", help="model name")

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
        default="./YOLOX/exps/default/yolox_l.py",
        type=str,
        help="pls input your experiment description file",
    )
    parser.add_argument("-c", "--ckpt", default=".//YOLOX/pretrainedmodel/yolox_l.pth", type=str, help="ckpt for eval")
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


def image_demo(predictor, vis_folder, path, current_time, save_result):
    if os.path.isdir(path):
        files = get_image_list(path)
    else:
        files = [path]
    files.sort()
    for image_name in files:
        outputs, img_info = predictor.inference(image_name)
        result_image = predictor.visual(outputs[0], img_info, predictor.confthre)
        print("shape: ", result_image.shape)
        if save_result:
            save_folder = os.path.join(
                vis_folder, time.strftime("%Y_%m_%d_%H_%M_%S", current_time)
            )
            os.makedirs(save_folder, exist_ok=True)
            save_file_name = os.path.join(save_folder, os.path.basename(image_name))
            logger.info("Saving detection result in {}".format(save_file_name))
            cv2.imwrite(save_file_name, result_image)
            # cv2.imshow("test", result_image)
        ch = cv2.waitKey(0)
        if ch == 27 or ch == ord("q") or ch == ord("Q"):
            break


def imageflow_demo(predictor, vis_folder, current_time, args):
    cap = cv2.VideoCapture(args.path if args.demo == "video" else args.camid)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # float
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float
    fps = cap.get(cv2.CAP_PROP_FPS)
    save_folder = os.path.join(
        vis_folder, time.strftime("%Y_%m_%d_%H_%M_%S", current_time)
    )
    os.makedirs(save_folder, exist_ok=True)
    if args.demo == "video":
        save_path = os.path.join(save_folder, args.path.split("/")[-1])
    else:
        save_path = os.path.join(save_folder, "camera.mp4")
    logger.info(f"video save_path is {save_path}")
    vid_writer = cv2.VideoWriter(
        save_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (int(width), int(height))
    )
    while True:
        ret_val, frame = cap.read()
        if ret_val:
            outputs, img_info = predictor.inference(frame)
            result_frame = predictor.visual(outputs[0], img_info, predictor.confthre)
            if args.save_result:
                vid_writer.write(result_frame)
            ch = cv2.waitKey(1)
            if ch == 27 or ch == ord("q") or ch == ord("Q"):
                break
        else:
            break

def driving_runtime(predictor, vis_folder, image, args, MyCar):
    # detection model inference 
    outputs, img_info = predictor.inference(image)

    # initilization of left, mid and right detection distance 
    distance_left = torch.tensor(float('inf'))
    distance_mid = torch.tensor(float('inf'))
    distance_right = torch.tensor(float('inf'))
    
    """
    When detecting the bounding boxes, enter this branch.
    Judging the left, mid and right bounding boxes
    in order to estimate the distance between autonomous driving vehicle and front vehicles.
    """
    if outputs[0] is not None:
        # initialize the index of left and right boundig boxes
        # if index number is not -1, there are vehicles in front of the autonomous deving vehicle.
        left_index = -1      
        left_position = -1   # 0 - 1
        right_index = -1
        right_position = 641 # image width pixel is 640 

        leftlist1 = []
        leftlist2 = []
        rightlist1 = []
        rightlist2 = []

        # first traversal 
        for i in range(outputs[0].shape[0]): 
            centroidX = outputs[0][i][0] + (outputs[0][i][2] - outputs[0][i][0]) / 2
            bottomY = outputs[0][i][3]
            if outputs[0][i][4] * outputs[0][i][5] > predictor.confthre and \
                (outputs[0][i][6] == 2 or outputs[0][i][6] == 7 or outputs[0][i][6] == 5 or outputs[0][i][6] == 6):
                if (MyCar.midlane == 0 or MyCar.midlane == -7) and \
                    MyCar.changing == False and \
                    centroidX <= args.leftbound: 
                    left_index = i 
                    leftlist1.append(i)
                    leftlist2.append( (outputs[0][i][2] - outputs[0][i][0]) * (outputs[0][i][3] - outputs[0][i][1]) )
                    # if outputs[0][i][2] - outputs[0][i][0] > 90:
                    #     left_index = i

            if (MyCar.midlane == 0 or MyCar.midlane == 7) and \
                    MyCar.changing == False and \
                    centroidX >= args.rightbound:
                    rightlist1.append(i)
                    rightlist2.append( (outputs[0][i][2] - outputs[0][i][0]) * (outputs[0][i][3] - outputs[0][i][1]) )
                    # if centroidX < right_position:
                    #     right_index = i
                    # if outputs[0][i][2] - outputs[0][i][0] > 90:
                    #     right_index = i
        if leftlist2:
            maxvalue_left = max(leftlist2)
            max_left_index = leftlist2.index(maxvalue_left)
            left_index = leftlist1[max_left_index]
        if rightlist2:
            maxvalue_right = max(rightlist2)
            max_right_index = rightlist2.index(maxvalue_right)
            right_index = rightlist1[max_right_index]

        
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
        
        # second traversal
        for i in range(outputs[0].shape[0]):
            # class name is car or truck, and score greater than threshold
            if outputs[0][i][4] * outputs[0][i][5] > predictor.confthre and \
                (outputs[0][i][6] == 2 or outputs[0][i][6] == 7 or outputs[0][i][6] == 5 or outputs[0][i][6] == 6):

                centroidX = outputs[0][i][0] + (outputs[0][i][2] - outputs[0][i][0]) / 2
                bottomY = outputs[0][i][3]

                if centroidX > args.leftbound and centroidX < args.rightbound and bottomY < 350:
                    distance_mid = distance_estimation(outputs[0][i][0].cpu().clone(), 
                                                        outputs[0][i][1].cpu().clone(), 
                                                        outputs[0][i][2].cpu().clone(), 
                                                        outputs[0][i][3].cpu().clone(), 
                                                        args)
                if outputs[0][i][2] - outputs[0][i][0] > 230 and bottomY < 390:
                    distance_mid = distance_estimation(outputs[0][i][0].cpu().clone(), 
                                                        outputs[0][i][1].cpu().clone(), 
                                                        outputs[0][i][2].cpu().clone(), 
                                                        outputs[0][i][3].cpu().clone(), 
                                                        args)
                    # print(i, distance)
                                        
    result_image = predictor.visual(outputs[0], img_info, predictor.confthre)
    img = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)
    # cv2.putText(img,"wei", (225, 100), 1, 2, (0,0,0))
    templeft = args.leftbound // 1.3333
    tempright = args.rightbound // 1.333
    cv2.line(img, (227, 100), (227, 300), (0,0,0), 1, 4)
    cv2.line(img, (252, 100), (252, 300), (0,0,0), 1, 4)
    cv2.imshow("AfterProcessing", img)
    cv2.waitKey(1)

    return distance_left,  distance_mid, distance_right


def main(exp, args):
    if not args.experiment_name:
        args.experiment_name = exp.exp_name

    file_name = os.path.join(exp.output_dir, args.experiment_name)
    os.makedirs(file_name, exist_ok=True)

    vis_folder = None
    if args.save_result:
        vis_folder = os.path.join(file_name, "vis_res")
        os.makedirs(vis_folder, exist_ok=True)

    if args.trt:
        args.device = "gpu"

    logger.info("Args: {}".format(args))

    if args.conf is not None:
        exp.test_conf = args.conf
    if args.nms is not None:
        exp.nmsthre = args.nms
    if args.tsize is not None:
        exp.test_size = (args.tsize, args.tsize)

    model = exp.get_model()
    logger.info("Model Summary: {}".format(get_model_info(model, exp.test_size)))

    if args.device == "gpu":
        model.cuda()
        if args.fp16:
            model.half()  # to FP16
    model.eval()

    if not args.trt:
        if args.ckpt is None:
            ckpt_file = os.path.join(file_name, "best_ckpt.pth")
        else:
            ckpt_file = args.ckpt
        logger.info("loading checkpoint")
        ckpt = torch.load(ckpt_file, map_location="cpu")
        # load the model state dict
        model.load_state_dict(ckpt["model"])
        logger.info("loaded checkpoint done.")

    if args.fuse:
        logger.info("\tFusing model...")
        model = fuse_model(model)

    if args.trt:
        assert not args.fuse, "TensorRT model is not support model fusing!"
        trt_file = os.path.join(file_name, "model_trt.pth")
        assert os.path.exists(
            trt_file
        ), "TensorRT model is not found!\n Run python3 tools/trt.py first!"
        model.head.decode_in_inference = False
        decoder = model.head.decode_outputs
        logger.info("Using TensorRT to inference")
    else:
        trt_file = None
        decoder = None

    predictor = Predictor(model, exp, COCO_CLASSES, trt_file, decoder, args.device, args.fp16, args.legacy)
    current_time = time.localtime()
    if args.demo == "image":
        image_demo(predictor, vis_folder, args.path, current_time, args.save_result)
    elif args.demo == "video" or args.demo == "webcam":
        imageflow_demo(predictor, vis_folder, current_time, args)
    elif args.demo == "driving":
        driving_runtime(predictor, vis_folder, image, args)



if __name__ == "__main__":
    args = make_parser().parse_args()
    exp = get_exp(args.exp_file, args.name)

    main(exp, args)
