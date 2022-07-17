'''
basic usage:
python epubimagereducer.py PATH(to epub)
will default to 30 jpeg qual, 5 png compression with no downscaling of images
'''

import sys
from time import strftime, localtime, time
import ctypes
import os
import argparse
import zipfile as zp
import cv2
import numpy as np
from msvcrt import getch as rawinput
from PIL import Image

version = "2"
app_name = "epubimagereducer"

class KEYMAP:
    # integers are open cv codes byte values are from msvcrt
    EXIT_KEYS = [27, 3, -1, b'\x03', b'\x1b'] # escape, ctrl c, closing window
    PREV_IMG = [b'K', b'H', 2490368, 2424832] # up left arrow keys
    NEXT_IMG = [b'M', b'P', 2555904, 2621440] # down right arrow keys 
    ACCEPT = [13] # ender
    INCREMENT_SCALE_S = [119]       # w
    INCREMENT_SCALE_L = [87]        # shift w
    DECREMENT_SCALE_S = [115]       # s
    DECREMENT_SCALE_L = [83]        # shift s
    INCREMENT_COMPRESSION_S = [101]    # e
    INCREMENT_COMPRESSION_L = [69]    # shift e
    DECREMENT_COMPRESSION_S = [100]    # d
    DECREMENT_COMPRESSION_L = [68]    # shift d

    
'''
TODO future versions
# use the actual logging library
# check non valid epubs dont break 
# check if you can input resolution correctly
# check it doesnt break if for some reason an image isn't "name.type", check .split(".") methods
# make tester support formats other than jpeg
'''

def logger(s, newline=True):
    timestamp = strftime("%Y/%m/%d %H:%M:%S ", localtime()) 
    _s = f"{app_name} v{version}: " + s
    with open(f"{app_name}log.txt", mode='a') as l:
        l.write(timestamp + _s + "\n")
        print(_s)

def main():
    os.chdir(r"C:\Users\AZM\Documents\Python\epubimagereducer")
    logger(f"Started with arguments: {sys.argv}")

    parser = argparse.ArgumentParser(description="Reduce image size for ePubs.")
    parser.add_argument("path", metavar="PATH", type=str, help="input file path to the .epub")
    # iphone res is [1334, 750] but no need cuz compression is a lot more relevant
    parser.add_argument("-res", type=int, nargs=2, help="resolution height to reduce the images to")
    parser.add_argument("-scale", type=int, help="scale by which to reduce the images, %")
    parser.add_argument("-jpeg-qual", type=int, default=30, help="jpeg quality level, default=30")
    parser.add_argument("-png-comp", type=int, default=5, help="png compression level, default=5")
    parser.add_argument("-test", action="store_true", help="enable test mode to help pick compression level")
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        ctypes.windll.user32.MessageBoxW(None, u"Requested file not found", app_name, 0)
        logger("Requested file not found, exited")
        exit()

    if args.test:
        logger("Using test mode")
        testmode(args.path)
        logger("Exiting")
        exit()

    orig_size = int(os.path.getsize(args.path)/1024)
    logger(f"Original file is {orig_size}kb.")
    outpath = args.path.split(".")[0] + "_c." + args.path.split(".")[1]
    
    with zp.ZipFile(args.path, 'r') as in_epub:
        with zp.ZipFile(outpath, 'w') as out_epub:
            for name in in_epub.namelist():
                with in_epub.open(name, "r") as file:
                    content = file.read()
                    if (name.startswith("OEBPS/Images/") or name.startswith("OEBPS/images/")) and (name != "OEBPS/Images/" or name != "OEBPS/images/"):
                        try:
                            _, type = name.split(".")
                        except ValueError as e:
                            logger(f"Something went wrong when attempting to check file: {name}")
                            print(e)
                            continue
                        if type in {"jpeg", "jpg", "png"}:
                            filesize = int(sys.getsizeof(content)/1024)
                            logger(f"Checking {name}: {filesize}kb")
                            image = cv2.imdecode(np.asarray(bytearray(content), dtype="uint8"), cv2.IMREAD_COLOR)
                            content = reduceImage(name, image, args.res,  args.jpeg_qual, args.png_comp, args.scale)
                            filesize = int(sys.getsizeof(content)/1024)
                            logger(f"Reduced {name} to {filesize}kb")
                        else:
                            ctypes.windll.user32.MessageBoxW(None, u"Unexpected file found, {}, ignoring.".format(name), app_name, 0)
                            logger(f"Unexpected file found, {name}, ignoring")
                    out_epub.writestr(name, content)
    
    end_size = int(os.path.getsize(outpath)/1024)
    logger(f"Finished file is {end_size}kb, {int(100 - (end_size/orig_size*100))}% reduction")

def reduceImage(name, image, target_res, jpeg_qual, png_comp, scale):
    if target_res or scale:
        image = downscale(name, image, target_res, scale)

    type = name.split(".")[1]

    if type == "jpg" or type == "jpeg":
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_qual]
    elif type == "png":
        encode_param = [int(cv2.IMWRITE_PNG_COMPRESSION), png_comp]
    return cv2.imencode(f".{type}", image, encode_param)[1].tobytes()

def downscale(name, image, target_res, scale):
    logger(f"{name} is {image.shape}")
    if not target_res:
        target_res = image.shape[0], image.shape[1]
    if not scale:
        scale = 100
    scale = min(target_res[0]/image.shape[0], target_res[1]/image.shape[1], scale/100)

    if scale >= 1:
        logger(f"{name} is small enough, passing")
        return image
    else:
        height = int(image.shape[0] * scale)
        width = int(image.shape[1] * scale)
        dim = (width, height)
        resized_image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        logger(f"Resized {name} to {resized_image.shape}")
        return resized_image

def testmode(path):
    # find all images
    orig_size = int(os.path.getsize(path)/1024)
    with zp.ZipFile(path, 'r') as in_epub:
        images = []
        for name in in_epub.namelist():
            with in_epub.open(name, "r") as file:
                if (name.startswith("OEBPS/Images/") or name.startswith("OEBPS/images/")) and (name != "OEBPS/Images/" or name != "OEBPS/images/"):
                    _, type = name.split(".")
                    if type in {"jpeg", "jpg", "png"}:
                        images.append(name)
    logger(f"Found {len(images)} images. Use arrow keys to browse")
    
    current = 0
    scale = 100
    comp = 100
    userin = 0
    with zp.ZipFile(path, 'r') as in_epub:
        while 1 :
            with in_epub.open(images[current], "r") as file:
                logger(f"Showing image {current}: {images[current]}, change with arrow keys")
                logger(f"Image at {scale}% and {comp} qual, change scale with w/s and qual with e/d, use shift to increase amount changed") # check KEYMAP class
                content = file.read()
                filesize0 = int(sys.getsizeof(content)/1024)
                image = cv2.imdecode(np.asarray(bytearray(content), dtype="uint8"), cv2.IMREAD_COLOR)
                content = reduceImage("Image.jpeg", image, (100000, 100000), comp, 5, scale)
                edit = cv2.imdecode(np.asarray(bytearray(content), dtype="uint8"), cv2.IMREAD_COLOR)
                filesize = int(sys.getsizeof(content)/1024)
                logger(f"Finished file is {filesize}kb from {filesize0}kb, {int(100 - (filesize/filesize0*100))}% reduction")
                cv2.imshow("Image", edit)
                userin = cv2.waitKeyEx()
                if userin in KEYMAP.EXIT_KEYS:
                    return
                if userin in KEYMAP.PREV_IMG:
                    current -= 1 if current > 0 else 0
                if userin in KEYMAP.NEXT_IMG:
                    current += 1 if current < len(images)-1 else -(len(images)-1)
                if userin in KEYMAP.ACCEPT:
                    break
                if userin in KEYMAP.INCREMENT_SCALE_S:
                    scale += 1
                if userin in KEYMAP.INCREMENT_SCALE_L:
                    scale += 10
                if userin in KEYMAP.DECREMENT_SCALE_S:
                    scale -= 1
                if userin in KEYMAP.DECREMENT_SCALE_L:
                    scale -= 10
                if scale > 100: scale = 100
                if scale < 1: scale = 1
                if userin in KEYMAP.INCREMENT_COMPRESSION_S:
                    comp += 1
                if userin in KEYMAP.INCREMENT_COMPRESSION_L:
                    comp += 10
                if userin in KEYMAP.DECREMENT_COMPRESSION_S:
                    comp -= 1
                if userin in KEYMAP.DECREMENT_COMPRESSION_L:
                    comp -= 10
                if comp > 100: comp = 100
                if comp < 1: comp = 1

if __name__ == '__main__':
    main()