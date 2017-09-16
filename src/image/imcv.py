"""
Using OpenCv to handle the Image operation
"""
import logging
import sys
import time

import numpy as np
import cv2

sys.path.append('../..')
from src.support.profiling import func_profiling

LOGGER = logging.getLogger(__name__)

class ImageCV(object):
    def __init__(self):
        super().__init__()

    @staticmethod
    @func_profiling
    def get_grayscale_image(image_path):
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    @staticmethod
    @func_profiling
    def get_edge_image(image_path, threshold1=50, threshold2=100):
        img = ImageCV.get_grayscale_image(image_path)
        img = cv2.Canny(img, threshold1, threshold2)
        return img

    @staticmethod
    @func_profiling
    def fill_connected_component(image, contour, threshold=255):
        """get the filled connected component"""
        cmp_img = np.zeros_like(image)
        cmp_img[contour] = image[contour]
        cmp_img = cv2.cvtColor(cmp_img, cv2.COLOR_BGR2GRAY)
        cmp_img, cnt, hierarchy = cv2.findContours(
            cmp_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cmp_img = np.zeros_like(cmp_img)
        cv2.drawContours(cmp_img, cnt, -1, threshold, -1)
        return cmp_img, cnt

    @staticmethod
    @func_profiling
    def connected_component_by_stats(threshold, nth, by):
        """
        return nth connected component by the value in stat matrix
        in descending sequences
            cv2.CC_STAT_LEFT The leftmost (x) coordinate
            cv2.CC_STAT_TOP The topmost (y) coordinate
            cv2.CC_STAT_WIDTH The horizontal size of the bounding box
            cv2.CC_STAT_HEIGHT The vertical size of the bounding box
            cv2.CC_STAT_AREA The total area (in pixels) of the connected component
        """
        output = cv2.connectedComponentsWithStats(threshold, 4, cv2.CV_32S)
        assert by in [
            cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP,
            cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT, cv2.CC_STAT_AREA]
        if 0 >= nth or nth >= output[0]:
            return

        cond_sequence = [(i ,output[2][i][by]) for i in range(output[0]) if i != 0]
        cond_sequence = sorted(cond_sequence, key=lambda x: x[1], reverse=True)
        return np.where(output[1] == cond_sequence[nth-1][0])

    @staticmethod
    def show_image_by_cv2(image, exit_code=27):
        """show image by cv2"""
        winname = str(hash(time.time()))
        cv2.namedWindow(winname)
        while True:
            cv2.imshow(winname, image)
            k = cv2.waitKey(0)
            if k == exit_code:
                break
        cv2.destroyAllWindows()
