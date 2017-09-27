"""
Defined callback functions of mouse event
"""
import logging
import sys

import cv2
import numpy as np

sys.path.append('../')
from src import tkconfig
from src.support.profiling import func_profiling
from src.support.tkconvert import TkConverter
from src.view.template import GraphcutViewer, ImageViewer, PreprocessViewer

LOGGER = logging.getLogger(__name__)

class MouseHandler(ImageViewer):
    def __init__(self):
        super().__init__()

class PreprocessMouse(MouseHandler, PreprocessViewer):
    def __init__(self):
        super().__init__()

class GraphcutMouse(MouseHandler, GraphcutViewer):
    def __init__(self):
        super().__init__()

    @func_profiling
    def draw_symmetric_line(self, event=None, color=255):
        enter_mirror = ('edit' in self.root_state and 'mirror' not in self.root_state)
        in_mirror = ('edit' in self.root_state and
                     'mirror' in self.root_state and
                     'seperate' not in self.root_state)
        if enter_mirror and self.symmetric_line:
            self.root_state.append('mirror')

        if in_mirror and self.symmetric_line:
            LOGGER.debug('mouse on label_image at {}'.format((event.x, event.y)))
            self.body_width = abs(event.x - self.symmetric_line[0][0])
