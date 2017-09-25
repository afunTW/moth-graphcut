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
    def read_and_convert_to_gray_image(image_path):
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    @staticmethod
    @func_profiling
    def read_and_convert_to_edge_image(image_path, threshold1=50, threshold2=100):
        img = ImageCV.read_and_convert_to_gray_image(image_path)
        img = cv2.Canny(img, threshold1, threshold2)
        return img

    @staticmethod
    @func_profiling
    def generate_error_mask(image, gamma=0.22):
        h, w = image.shape[0], image.shape[1]
        image = image.astype('float64')
        image[:] *= 0.22
        font = cv2.FONT_HERSHEY_TRIPLEX
        cv2.putText(image, 'Error', (int(w/3), int(h/2)), font, 3, (0, 0, 255), 3)
        return image

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

    # image preprocess: get the object by difference
    @staticmethod
    @func_profiling
    def run_floodfill(image, threshold=0.9):
        original_image = image.copy()

        # get the magnitude
        img_float32 = original_image.astype('floar32') / 255.0
        img_gradient_x = cv2.Sobel(img_float32, cv2.CV_32F, 1, 0, ksize=1)
        img_gradient_y = cv2.Sobel(img_float32, cv2.CV_32F, 0, 1, ksize=1)
        mag, angle = cv2.cartToPolar(img_gradient_x, img_gradient_y, angleInDegrees=Trye)

        # normalize
        mag += max(-mag.min(), 0)
        mag /= mag.max()
        mag *= 255
        image = mag.astype('uint8')

        # binary threshold
        threshold_value = np.sort(image, axis=None)[int(image.size*threshold)]
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, image = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY)

        # floodfill and reverse
        img_floodfill = original_image.copy()
        mask_h, mask_w = img_floodfill.shape[0]+2, img_floodfill.shape[1]+2
        mask = np.zeros((mask_h, mask_w), np.uint8)
        cv2.floodfill(img_floodfill, mask, (0, 0), 255)
        img_floodfill_rev = cv2.bitwise_not(img_floodfill)

        # result image
        img_out = original_image | img_floodfill_rev
