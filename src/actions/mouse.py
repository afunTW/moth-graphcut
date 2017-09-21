"""
Defined callback functions of mouse event
"""
import logging
import sys

import cv2
import numpy as np

sys.path.append('../')
from src.view.template import MothViewerTemplate
from src.support.profiling import func_profiling
from src.support.tkconvert import TkConverter

LOGGER = logging.getLogger(__name__)

class MothMouseHandler(MothViewerTemplate):
    def __init__(self):
        super().__init__()

    # @func_profiling
    # def draw_symmetric_line(self, event=None, color=255):
    #     LOGGER.debug('mouse on label_image at {}'.format((event.x, event.y)))
    #     # draw the line by OpenCV
    #     h, w, channels = self.image_panel_tmp.shape
    #     cv2.line(self.image_panel_tmp, (event.x, 0), (event.x, h), color, 2)
    #     self._update_image(edit_mode=True)
