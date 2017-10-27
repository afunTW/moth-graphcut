import glob
import json
import logging
import os
import sys
from inspect import currentframe, getframeinfo

import numpy as np

import cv2
from matplotlib import pyplot as plt

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)


# test fore_left
def test():
    # DIR_MOTH = os.path.abspath(os.path.join(__FILE__, '../image/thermal/original_rgb/_SWU9909_floodfill/'))
    # FILES_MOTH = glob.glob(os.path.join(DIR_MOTH, '*.png'))
    DIR_THERMAL = '/home/dirl/github/moth-graphcut/image/thermal/original_temp_txt/0001/'
    FILES_THERMAL = glob.glob(os.path.join(DIR_THERMAL, '*.txt'))
    FILE_MOTH_META = '/home/dirl/github/moth-graphcut/image/thermal/original_rgb/_SWU9909_floodfill/_SWU9909_floodfill.json'
    FILE_TRANSFORM_MATRIX = '/home/dirl/github/moth-graphcut/image/thermal/original_rgb/_SWU9909/transform_matrix.dat'
    test_foreleft = '/home/dirl/github/moth-graphcut/image/thermal/original_rgb/_SWU9909_floodfill/_SWU9909_floodfill_fore_left.png'
    mat_thermal = sorted(FILES_THERMAL, key=lambda x: int(x.split(os.sep)[-1].split('.')[0].split('_')[-1]))
    with open(FILE_MOTH_META, 'r') as f:
        meta = json.load(f)

    # load image and transform matrix
    cnt_foreleft = meta['components_contour']['forewings']['left']
    img_foreleft = cv2.imread(test_foreleft)
    mat_test_thermal = np.loadtxt(open(mat_thermal[0], 'rb'), delimiter=',', skiprows=1)
    transform_matrix = np.fromfile(FILE_TRANSFORM_MATRIX)
    transform_matrix = transform_matrix.reshape(3,3)

    # original image preprocess
    img_resize_foreleft = cv2.resize(img_foreleft, mat_test_thermal.shape[:2][::-1])
    img_resize_foreleft = cv2.cvtColor(img_resize_foreleft, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(img_resize_foreleft, 0, 255, cv2.THRESH_BINARY)
    src, contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # thermal image preprocess
    mat_warp_thermal = cv2.warpPerspective(mat_test_thermal, transform_matrix, mat_test_thermal.shape[:2][::-1])
    mat_warp_thermal.

    # check
    rgb_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    cv2.drawContours(rgb_mask, contours, 0, (255, 0, 0), 2)
    plt.imshow(rgb_mask); plt.show()

def main():
    test()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    main()
