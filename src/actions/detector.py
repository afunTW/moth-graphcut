import logging
import sys

import cv2
import numpy as np

sys.path.append('../..')
from src.image.imcv import ImageCV
from src.support.profiling import func_profiling

LOGGER = logging.getLogger(__name__)
DETECT_METHOD = [cv2.TM_CCOEFF, cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR,\
                 cv2.TM_CCORR_NORMED, cv2.TM_SQDIFF,cv2.TM_SQDIFF_NORMED]

class TemplateDetector(object):
    """
    Argument
        @template:  template image path
        @target:    the image path which you want to detect the template
    """
    def __init__(self, template, target):
        super().__init__()
        self.template = template
        self.target = target
        self._template_canny = ImageCV.read_and_convert_to_edge_image(template)
        self._target_gray = ImageCV.read_and_convert_to_gray_image(target)
        self._found = None

    def ptx_to_rect(self, pos1, pos2):
        x = min(pos1[0], pos2[0])
        y = min(pos1[1], pos2[1])
        w = abs(pos1[0] - pos2[0])
        h = abs(pos1[1] - pos2[1])
        return (x, y, w, h)

    def detect_template(self, method=cv2.TM_CCOEFF):
        over_size = lambda x, y: x.shape[0] < y.shape[0] or x.shape[1] < y.shape[1]

        if method in DETECT_METHOD:
            self._found = None

            # multiscale
            for scale in np.linspace(0.5, 1.0, 32)[::-1]:
                template_h, template_w = self._template_canny.shape
                target_h, target_w = self._target_gray.shape
                dimention = (int(target_w*scale), int(target_h*scale))
                resized_target = cv2.resize(self._target_gray, dimention, interpolation=cv2.INTER_AREA)
                ratio = target_w / float(resized_target.shape[1])

                if over_size(resized_target, self._template_canny):
                    break

                target_canny = cv2.Canny(resized_target, 50, 200)
                match_result = cv2.matchTemplate(target_canny, self._template_canny, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_result)

                # get the maximum correlation value
                if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                    if self._found is None or min_val < self._found[0]:
                        self._found = (min_val, min_loc, ratio)
                else:
                    if self._found is None or max_val > self._found[0]:
                        self._found = (max_val, max_loc, ratio)

            template_h, template_w = self._template_canny.shape
            val, loc, r = self._found
            top_left = (int(loc[0]*r), int(loc[1]*r))
            bottom_right = (int((loc[0]+template_w)*r), int((loc[1]+template_h)*r))
            rect =  self.ptx_to_rect(top_left, bottom_right)
            return rect

        else:
            LOGGER.error('INput method {} is not defined'.format(method))

    def detect_rectangle(self, focus_rect=None):
        self._target_gray[np.where(self._target_gray > [5])] = 120
        target_threshold = cv2.threshold(self._target_gray, 60, 255, cv2.THRESH_BINARY)[1]
        cnts = cv2.findContours(target_threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[1]
        possible_rects = []

        for i, cnt in enumerate(cnts):
            perimeter = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.003*perimeter, True)
            x, y, w, h = cv2.boundingRect(approx)

            if focus_rect is not None and isinstance(focus_rect, tuple) and len(focus_rect) == 4:
                X, Y, W, H = focus_rect
                if X<x<x+w<X+W and Y<y<y+h<Y+H:
                    possible_rects.append((x, y, w, h))
            else:
                possible_rects.append((x, y, w, h))
        return possible_rects

if __name__ == '__main __':
    """testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
