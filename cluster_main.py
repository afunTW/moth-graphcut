import pickle
import logging
import numpy as np
import cv2
import sys
import os

sys.path.append('.')
from src import superpixel
from src import detector
from itertools import groupby
from itertools import chain
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries
from skimage.segmentation import active_contour
from skimage.util import img_as_float


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

# def antenna_filter(image, reverse=False):
#     img = image.copy()

#     kernel = np.ones((15, 15), np.float32) / 225
#     lower = np.array([0, 0, 0])
#     upper = np.array([240, 240, 240])
#     mask = cv2.inRange(image, lower, upper)
#     mask = cv2.dilate(mask, kernel, iterations = 1)

#     for i, row in enumerate(mask):
#         groups = [list(g) for k, g in groupby(row)]
#         index = [len(elt) for elt in groups]

#         if len(index) > 3:
#             index = np.cumsum(index)
#             if reverse:
#                 image[i, :index[-3]] = 255
#             else:
#                 image[i, index[2]:] = 255
#     return image

def main(filename, template=None, interactive=True, shift_x=None, shift_y=None):

    # filter
    orig_image = None
    if template:
        scale_detector = detector.ShapeDetector(template, filename)
        scale_detector.detect_template()
        orig_image = scale_detector.output

        if scale_detector.template_result:
            tx, ty, tw, th = scale_detector.template_result
            H, W, channels = scale_detector.output.shape
            scale_detector.detect_retangle(focus_rect=(0, ty, W, H-ty))

            scale_rects = filter_rects(
                scale_detector.rectangles, scale_detector.template_result)
            rect = is_bottom_right(scale_rects)

            x, y, w, h = scale_detector.template_result
            orig_image[y:y+h, x:x+w, :] = 255

            if rect:
                x, y, w, h = rect
                orig_image[y-5:y+h+5, x-5:x+w+5, :] = 255

    # superpixel
    img = superpixel.SuperPixel(filename, orig_image)
    img.segment = slic(
        img_as_float(img.orig_image), n_segments=2500, sigma=0.1)

    if shift_x:
        img.shift_x = shift_x
    if shift_y:
        img.shift_y = shift_y

    img.active(interactive=interactive)

    forewings = img.output[0] + img.output[1] - 255
    forewings, remained = img.fixed(forewings)
    padding = np.ones(remained.shape)*255
    padding[np.where(remained != [0])] = remained[np.where(remained != [0])]
    padding.astype('uint8')

    backwings = img.output[2] + img.output[3] - 255
    backwings[np.where(padding != [255])] = padding[np.where(padding != [255])]
    backwings, remained = img.fixed(backwings)
    return (img, np.hstack((img.image, forewings, backwings)))

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [ %(levelname)8s ] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )

    try:
        kmeans_path = os.path.abspath('./kmeans')
        kmeans_map = os.path.join(kmeans_path, 'all_shape_map.p')
        template_path = os.path.abspath('./10mm.png')

        with open(kmeans_map, 'rb') as f:
            cluster_map = pickle.load(f)
            logging.info('Load kmeans clustering map from %s' % kmeans_map)

        for i, cluster in cluster_map.items():
            saved_dir = os.path.abspath(os.path.join('.','results',str(i)))
            output = 'cluster_{0}_center.png'.format(i)
            output = os.path.join(saved_dir, output)

            if not os.path.exists(saved_dir):
                os.makedirs(saved_dir)
                logging.info('Create directory %s' % saved_dir)

            center = main(cluster['center'], template=template_path)
            cv2.imwrite(output, center[1])
            logging.info('cluster (%d/%d) center %s' % (i+1, len(cluster_map), output))

            for j, img in enumerate(cluster['neighbor']):

                output = 'cluster_{0}_neighbor_{1}.png'.format(i, j)
                output = os.path.join(saved_dir, output)
                neighbor = main(
                    img, template=template_path, interactive=False,
                    shift_x=center[0].shift_x, shift_y=center[0].shift_y)

                cv2.imwrite(output, neighbor[1])
                logging.info(
                    'cluster (%d/%d) neighbor (%d/%d) %s' %
                    (i+1, len(cluster_map), j+1, len(cluster['neighbor']), output))

    except Exception as e:
        logging.exception(e)
