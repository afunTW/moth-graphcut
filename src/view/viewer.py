"""
wrap the tkinter function for this project
"""
import logging
import sys
import time
import tkinter
from inspect import currentframe, getframeinfo
from os.path import abspath
sys.path.append('../..')

from PIL import Image, ImageTk

from tkconvert import TkConverter
from src.image.imnp import ImageNP

LOGGER = logging.getLogger(__name__)

class MothViewerTemplate(object):
    def __init__(self, image, winname=time.ctime()):
        super().__init__()

        """windows"""
        self.root = tkinter.Tk()
        self.root.wm_title(winname)

        """canvas"""
        try:
            self.image_panel = tkinter.PhotoImage(file=image)
            self._image_w, self._image_h = self.image_panel.width(), self.image_panel.height()
        except Exception as identifier:
            LOGGER.warning('Input Image not in the format of .gif, .pgm, .ppm')
            _im = Image.open(image)
            self._image_w, self._image_h = _im.size
            self.image_panel = ImageTk.PhotoImage(_im)
            self.image_display = ImageNP.generate_checkboard((self._image_h, self._image_w), block_size=10)
            self.image_display = TkConverter.ndarray_to_photo(self.image_display)

        self.canvas_panel = tkinter.Canvas(self.root, width=self._image_w, height=self._image_h)
        self.canvas_panel.create_image(0, 0, anchor='nw', image=self.image_panel)
        self.canvas_panel.pack(padx=10, fill='x', side='left')

        self.canvas_display = tkinter.Canvas(self.root, width=self._image_w, height=self._image_h)
        self.canvas_display.create_image(0, 0, anchor='nw', image=self.image_display)
        self.canvas_display.pack(padx=10, fill='x', side='right')

    def mainloop(self):
        self.root.mainloop()

if __name__ == '__main__':
    """testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
    _FILE = abspath(getframeinfo(currentframe()).filename)
    SAMPLE_IMG = abspath('../../image/sample/0.jpg')
    SAMPLE_IMG2 = abspath('../../image/sample/1.jpg')

    viewer = MothViewerTemplate(SAMPLE_IMG, winname=SAMPLE_IMG)
    viewer.mainloop()
