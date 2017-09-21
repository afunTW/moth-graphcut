"""
Defined callback functions of mouse event
"""
import logging
import sys

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
# def draw_symmetric_line_by_cv2(e, widget=None, image=None, color='255'):
#     if widget is None:
#         LOGGER.error('No widget has been selected.')
#     elif image is None:
#         LOGGER.error('No image has been selected.')
#         return None
#     elif not isinstance(image, np.ndarray):
#         LOGGER.error('Image {} is not in np.ndarray format.'.format(type(image)))
#         return None
#     else:
#         # draw the line by OpenCV
#         h, w, channels = image.shape
#         cv2.line(image, (e.x, 0), (e.x, h), color, 2)

#         # update the image to widget
#         photo = TkConverter.ndarray_to_photo(image)
#         widget.configure(image=photo)
