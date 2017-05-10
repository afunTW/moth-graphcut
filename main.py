import os
import sys
import cv2
import logging
import numpy as np

from src import detector
from src import graphic


def filter_rects(rects, ignore_rect):
    result = []
    ix, iy, iw, ih = ignore_rect

    for rect in rects:
        x, y, w, h = rect
        if ix<x<x+w<ix+iw and iy<y<y+h<iy+ih: continue
        else: result.append(rect)

    return result

def is_bottom_right(rects):
    result = None
    for rect in rects:
        if not result or (rect[0]+rect[2]) >= (result[0]+result[2]):
            result = rect
            continue
    return result

def main(filename, template=None):

    # filter
    orig_image = None
    if template:
        logging.info(' Process scale filter')
        scale_detector = detector.ShapeDetector(template, filename)
        scale_detector.detect_template()
        orig_image = scale_detector.output

        if scale_detector.template_result:
            logging.info('  * Filter template')
            tx, ty, tw, th = scale_detector.template_result
            H, W, channels = scale_detector.output.shape
            scale_detector.detect_retangle(focus_rect=(0, ty, W, H-ty))

            scale_rects = filter_rects(
                scale_detector.rectangles, scale_detector.template_result)
            rect = is_bottom_right(scale_rects)

            x, y, w, h = scale_detector.template_result
            orig_image[y:y+h, x:x+w, :] = 255

            if rect:
                logging.info('  * Filter scale')
                x, y, w, h = rect
                orig_image[y-5:y+h+5, x-5:x+w+5, :] = 255

    # graphic
    gb = graphic.GraphCut(filename, orig_image=orig_image)
    logging.info(' Process graph cut')
    gb.run()

    # mat = [[255. for w in range(600)] for h in range(400)]
    # for x, row in enumerate(mat):
    #     for y, column in enumerate(row):
    #         mat[x:y]
    # mat = np.array(mat)

    # cv2.imshow('test', gb.transparent_bg)
    # k = cv2.waitKey(0)
    # if k == 27: exit()
    # cv2.destroyAllWindows()

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [ %(levelname)8s ] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
    try:
        template_path = '10mm.png'
        '''
        moths_path = os.path.abspath('../img')
        moths = [os.path.join(moths_path, moth) for moth in os.listdir(moths_path)]

        for i, moth in enumerate(moths):
            logging.info(
                '({}/{}) Process {}'.format(i+1, len(moths), moth.split('/')[-1]))
            main(moth, template=template_path)
            break
        '''
        main('sample.jpg', template=template_path)

    except Exception as e:
        logging.exception(e)
