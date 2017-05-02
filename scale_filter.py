import os
import cv2
import sys
import numpy as np
import logging

sys.path.append('.')
from src import detector

def filter_rects(rects, ignore_rect):
    result = []
    ix, iy, iw, ih = ignore_rect

    for rect in rects:
        x, y, w, h = rect
        if ix<x<x+w<ix+iw and iy<y<y+h<iy+ih:
            continue
        else:
            result.append(rect)

    return result

def is_bottom_right(rects):
    result = None

    for rect in rects:
        if not result or (rect[0]+rect[2]) >= (result[0]+result[2]):
            result = rect
            continue

    return result

def main():
    image_path = os.path.abspath('../img')
    saved_path = os.path.abspath('../clearimg')
    template_path = os.path.abspath('./10mm.png')

    # list all demo filename
    moths = [
        os.path.join(image_path, img)
        for img in os.listdir(image_path)
        if os.path.isfile(os.path.join(image_path, img))
    ]

    if not os.path.exists(saved_path):
        os.makedirs(saved_path)

    for i, moth in enumerate(moths):
        scale_detector = detector.ShapeDetector(template_path, moth)
        scale_detector.detect_template()
        output = scale_detector.output
        outname = os.path.join(saved_path, '_'.join([str(i+1), moth.split('/')[-1]]))

        if scale_detector.template_result:
            tx, ty, tw, th = scale_detector.template_result
            H, W, channels = scale_detector.orig_image.shape
            scale_detector.detect_retangle(focus_rect=(0, ty, W, H-ty))

            scale_rects = filter_rects(
                scale_detector.rectangles, scale_detector.template_result)
            rect = is_bottom_right(scale_rects)

            # template rect
            x, y, w, h = scale_detector.template_result
            output[y:y+h, x:x+w, :] = 255
            # cv2.rectangle(output, (x,y), (x+w, y+h), scale_detector.RED, 2)

            # scale rects
            x, y, w, h = rect
            output[y-5:y+h+5, x-5:x+w+5, :] = 255
            # cv2.rectangle(output, (x,y), (x+w, y+h), scale_detector.BLUE, 2)

            cv2.imwrite(outname, output)
            logging.info('Saved ({}/{}) {}'.format(i+1, len(moths), outname))


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [ %(levelname)8s ] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )

    try:
        main()
    except Exception as e:
        logging.exception(e)
