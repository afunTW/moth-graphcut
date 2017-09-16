import logging
import sys
sys.path.append('../..')

import numpy as np

import cv2
from src.support.profiling import func_profiling
from src.image.imcv import ImageCV

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
        self._template = ImageCV.get_edge_image(template)
        self._target = ImageCV.get_grayscale_image(target)


if __name__ == '__main __':
    """testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
