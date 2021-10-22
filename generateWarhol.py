#!/usr/bin/python
# -*- coding: utf-8 -*-

# todo:
# line 74: function shift_hue removes transparency, so it can be changed to preserve it
# line 105: step (non-random) hue changing doesn't work in the HUE_MIN/HUE_MAX range


import argparse
import configparser
from PIL import Image
from PIL import ImageFilter
from PIL.ImageFilter import (BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE, EMBOSS, FIND_EDGES, SMOOTH, SMOOTH_MORE, SHARPEN)
import uuid
import numpy as np
import cv2
import random

def resolveConfigConflict(console_arg,config_arg):
    if(console_arg is not None):
        return console_arg
    else:
        return config_arg

def main(args):
    config = configparser.ConfigParser()
    config.read('config.ini')
    INPUT = resolveConfigConflict(args.input,config['BASIC']['INPUT'])
    PRIORITIZE_WIDTH = resolveConfigConflict(args.prioritize_width,bool(int(config['BASIC']['PRIORITIZE_WIDTH'])))
    TARGET_HEIGHT = resolveConfigConflict(args.target_height,int(config['BASIC']['TARGET_HEIGHT']))
    TARGET_WIDTH = resolveConfigConflict(args.target_width,int(config['BASIC']['TARGET_WIDTH']))
    GRID_SIZE = resolveConfigConflict(args.grid_size,int(config['BASIC']['GRID_SIZE']))

    USED_FILTERS = [eval(filt[0].upper()) for filt in config.items('FILTERS') if bool(int(filt[1]))]
    
    arg_filters = {BLUR: args.filter_blur, 
    CONTOUR: args.filter_contour, 
    DETAIL: args.filter_detail, 
    EMBOSS: args.filter_emboss, 
    SHARPEN: args.filter_sharpen, 
    FIND_EDGES: args.filter_find_edges, 
    SMOOTH: args.filter_smooth, 
    SMOOTH_MORE: args.filter_smooth_more, 
    EDGE_ENHANCE: args.filter_edge_enhance, 
    EDGE_ENHANCE_MORE: args.filter_edge_enhance_more}
    
    arg_filters_active = [filt[0] for filt in arg_filters.items() if filt[1]==True]
    
    if(len(arg_filters_active) > 0):
        USED_FILTERS = list(set(USED_FILTERS+arg_filters_active))
    
    HUE_RANDOM = resolveConfigConflict(args.hue_random,bool(int(config['HUE']['HUE_RANDOM'])))
    HUE_MIN = resolveConfigConflict(args.hue_min,float(config['HUE']['HUE_MIN']))
    HUE_MAX = resolveConfigConflict(args.hue_max,float(config['HUE']['HUE_MAX']))
    HUE_STEP = resolveConfigConflict(args.hue_step,float(config['HUE']['HUE_STEP']))
    HUE_APPEND = resolveConfigConflict(args.hue_append,bool(int(config['HUE']['HUE_APPEND'])))
    
    try:
        img = Image.open(INPUT)
    except:
        print("Something is wrong with the input file.")
        return
    
    def image_resize_to_height(img):
        width, height = img.size
        ratio = (TARGET_HEIGHT/GRID_SIZE)/height
        return img.resize((int(width*ratio), int(height*ratio)))

    def image_resize_to_width(img):
        width, height = img.size
        ratio = (TARGET_WIDTH/GRID_SIZE)/width
        return img.resize((int(width*ratio), int(height*ratio)))

    def shift_hue(img,angle):
        img_bgr = np.array(img)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        n_shift = angle // 2
        img_hsv[:, :, 0] = (img_hsv[:, :, 0].astype(int) + n_shift) % 181
        img_bgr_shifted = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
        return Image.fromarray(img_bgr_shifted)
        
    if PRIORITIZE_WIDTH:
        img_resized = image_resize_to_width(img)
    else:
        img_resized = image_resize_to_height(img)
    
    width, height = img_resized.size
    
    if not HUE_APPEND:
        img_resized2 = Image.new( mode = "RGB", size = (width, height))
        img_resized2 = img_resized.copy()
        
        
    
    img_finished = Image.new( mode = "RGBA", size = (width*GRID_SIZE, height*GRID_SIZE), color = (0,0,0,1) )
    hue_range = HUE_MAX - HUE_MIN
    hue_cur_step = HUE_STEP
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if (HUE_RANDOM):
                hue_cur_rand = HUE_MIN + random.random()*hue_range
                if(HUE_APPEND):
                    img_resized = shift_hue(img_resized,hue_cur_rand)
                else:
                    img_resized = shift_hue(img_resized2,hue_cur_rand)
            else:
                hue_next_step = HUE_STEP
                if(HUE_APPEND):
                    print(hue_cur_step)
                    img_resized = shift_hue(img_resized,hue_cur_step)
                else:
                    img_resized = shift_hue(img_resized2,hue_cur_step)
                    img_resized.show()
                hue_cur_step = hue_next_step
            if len(USED_FILTERS) > 0:
                try:
                    img_finished.paste(img_resized.filter(random.choice(USED_FILTERS)), (width*i,height*j))
                except:
                    print("Something is probably wrong with the filters.")
            else:
                img_finished.paste(img_resized, (width*i,height*j))
    filename = str(uuid.uuid4())
    img_finished.save("img/"+filename+".png")
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A program used to generate Warhol like pop portaits',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', dest='input', type=str, help='Filename to read from')
    parser.add_argument('--target-width', dest='target_width', type=int, help='Width of the resulting image in px. Needs --prioritize-width to be active')
    parser.add_argument('--target-height', dest='target_height', type=int, help='Height of the resulting image in px')
    parser.add_argument('-g', '--grid-size', dest='grid_size', type=int, help='NxN grid of input images')
    parser.add_argument('--prioritize-width', action=argparse.BooleanOptionalAction, dest='prioritize_width', help='Whether to scale according to the passed argument --target-width or --target-height')
    
    parser.add_argument('--blur', dest='filter_blur', action=argparse.BooleanOptionalAction)
    parser.add_argument('--contour', dest='filter_contour', action=argparse.BooleanOptionalAction)
    parser.add_argument('--detail', dest='filter_detail', action=argparse.BooleanOptionalAction)
    parser.add_argument('--emboss', dest='filter_emboss', action=argparse.BooleanOptionalAction)
    parser.add_argument('--sharpen', dest='filter_sharpen', action=argparse.BooleanOptionalAction)
    parser.add_argument('--find-edges', dest='filter_find_edges', action=argparse.BooleanOptionalAction)
    parser.add_argument('--smooth', dest='filter_smooth', action=argparse.BooleanOptionalAction)
    parser.add_argument('--smooth_more', dest='filter_smooth_more', action=argparse.BooleanOptionalAction)
    parser.add_argument('--edge_enhance', dest='filter_edge_enhance', action=argparse.BooleanOptionalAction)
    parser.add_argument('--edge_enhance_more', dest='filter_edge_enhance_more', action=argparse.BooleanOptionalAction)
    
    parser.add_argument('--hue-random', dest='hue_random', action=argparse.BooleanOptionalAction, help='Whether to generate hue randomly or not. If used, then --hue-step has no effect')
    parser.add_argument('--hue-min', dest='hue_min', type=float, help='The smallest allowed hue angle (google "HSV color wheel" to learn more)')
    parser.add_argument('--hue-max', dest='hue_max', type=float, help='The largest allowed hue angle (google "HSV color wheel" to learn more)')
    parser.add_argument('--hue-step', dest='hue_step', type=float, help='The hue difference step taken every other picture, works only if --hue-random is not being used)')
    parser.add_argument('--hue-append', dest='hue_append', action=argparse.BooleanOptionalAction, help='Whether to add up to the hue from the previous frame or not')
    args = parser.parse_args()
    main(args)