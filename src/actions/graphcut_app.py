import logging
import os
import sys
import tkinter
from inspect import currentframe, getframeinfo
from tkinter import ttk
from tkinter.filedialog import askopenfilenames
sys.path.append('../..')

import cv2
from src.view.graphcut_app import GraphCutViewer

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)
STATE = ['browse', 'edit']

class GraphCutAction(GraphCutViewer):
    def __init__(self):
        super().__init__()
        self.instruction = None
        self._image_queue = []
        self._current_image_info = {}
        self._current_state = None

        # callback
        self.scale_gamma.config(command=self._update_scale_gamma_msg)
        self.scale_manual_threshold.config(command=self._update_scale_manual_threshold_msg)

    # callback: drag the ttk.Scale and show the current value
    def _update_scale_gamma_msg(self, val_gamma):
        val_gamma = float(val_gamma)
        self.label_gamma.config(text=u'調整對比 ({:.2f}): '.format(val_gamma))

    # callback: drag the ttk.Scale and show the current value
    def _update_scale_manual_threshold_msg(self, val_threshold):
        val_threshold = float(val_threshold)
        self.label_manual_threshold.config(text=u'門檻值 ({:.2f}): '.format(val_threshold))

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    graphcut_action = GraphCutAction()
    graphcut_action.mainloop()
