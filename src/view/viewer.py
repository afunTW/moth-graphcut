"""
Wrap the tkinter function for this project
"""
import logging
import sys
import time
import tkinter
from inspect import currentframe, getframeinfo
from os.path import abspath
sys.path.append('../')

from PIL import Image, ImageTk

from image.imnp import ImageNP
from tkconvert import TkConverter
from tkfonts import TkFonts
from tkframe import TkFrame

LOGGER = logging.getLogger(__name__)

class MothViewerTemplate(object):
    def __init__(self, image, winname=time.ctime()):
        super().__init__()
        self.root = tkinter.Tk()
        self.root.wm_title(winname)

        """Frame init"""
        self.frame_root = TkFrame(self.root, bg='white')
        self.frame_nav = TkFrame(self.frame_root, bg='orange')
        self.frame_body = TkFrame(self.frame_root, bg='black')
        self.frame_footer = TkFrame(self.frame_root, bg='yellow')
        self.frame_panel = TkFrame(self.frame_body, bg='red')
        self.frame_display = TkFrame(self.frame_body, bg='blue')
        self.frame_label_panel_text = TkFrame(self.frame_panel)
        self.frame_label_panel_image = TkFrame(self.frame_panel)
        self.frame_label_display_text = TkFrame(self.frame_display)
        self.frame_label_display_image = TkFrame(self.frame_display)
        self.frame_trackbar_gamma = TkFrame(self.frame_footer)
        self.frame_trackbar_threshold = TkFrame(self.frame_footer)

        """Widget manager"""
        self.frame_root.grid(row=0, column=0)
        self.frame_nav.grid(row=0, column=0)
        self.frame_body.grid(row=1, column=0)
        self.frame_footer.grid(row=2, column=0)
        self.frame_panel.grid(row=0, column=0)
        self.frame_display.grid(row=0, column=1)
        self.frame_label_panel_text.grid(row=0, column=0)
        self.frame_label_panel_image.grid(row=1, column=0)
        self.frame_label_display_text.grid(row=0, column=0)
        self.frame_label_display_image.grid(row=1, column=0)
        self.frame_trackbar_gamma.grid(row=0, column=0)
        self.frame_trackbar_threshold.grid(row=1, column=0)

        """Layout of container"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        """Label"""
        from tkinter import ttk
        self._font = TkFonts()
        self.label_panel = ttk.Label(self.frame_label_panel_text, text='Input Panel', font=self._font.h2())
        self.label_display = ttk.Label(self.frame_label_display_text, text='Display', font=self._font.h2())
        self.label_panel.grid(sticky='news')
        self.label_display.grid(sticky='news')

        """Canvas"""
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

        self.label_panel_image = ttk.Label(self.frame_label_panel_image, image=self.image_panel)
        self.label_panel_image.grid(row=0, column=0, sticky='news')
        self.label_display_image = ttk.Label(self.frame_label_display_image, image=self.image_display)
        self.label_display_image.grid(row=0, column=0, sticky='news')

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
