"""
Wrap the tkinter function for this project
"""
import logging
import sys
import time
import tkinter
from inspect import currentframe, getframeinfo
from os.path import abspath
sys.path.append('../..')

from PIL import Image, ImageTk

from src.image.imnp import ImageNP
from tkconvert import TkConverter
from tkfonts import TkFonts

LOGGER = logging.getLogger(__name__)

class MothViewerTemplate(object):
    def __init__(self, image, winname=time.ctime()):
        super().__init__()
        self.root = tkinter.Tk()
        self.root.wm_title(winname)

        """Frame init"""
        self.frame_root = tkinter.Frame(self.root, bg='white')
        self.frame_nav = tkinter.Frame(self.frame_root, bg='orange')
        self.frame_body = tkinter.Frame(self.frame_root, bg='black')
        self.frame_footer = tkinter.Frame(self.frame_root, bg='yellow')
        self.frame_panel = tkinter.Frame(self.frame_body, bg='red')
        self.frame_display = tkinter.Frame(self.frame_body, bg='blue')
        self.frame_label_panel = tkinter.Frame(self.frame_panel)
        self.frame_canvas_panel = tkinter.Frame(self.frame_panel)
        self.frame_label_display = tkinter.Frame(self.frame_display)
        self.frame_canvas_display = tkinter.Frame(self.frame_display)
        self.frame_trackbar_gamma = tkinter.Frame(self.frame_footer)
        self.frame_trackbar_threshold = tkinter.Frame(self.frame_footer)

        """Widget manager"""
        self.frame_root.grid(row=0, column=0, sticky='news')
        self.frame_nav.grid(row=0, column=0, sticky='news')
        self.frame_body.grid(row=1, column=0, sticky='news')
        self.frame_footer.grid(row=2, column=0, sticky='news')
        self.frame_panel.grid(row=0, column=0, sticky='news')
        self.frame_display.grid(row=0, column=1, sticky='news')
        self.frame_label_panel.grid(row=0, column=0, sticky='ew')
        self.frame_canvas_panel.grid(row=1, column=0, sticky='ew')
        self.frame_label_display.grid(row=0, column=0, sticky='ew')
        self.frame_canvas_display.grid(row=1, column=0, sticky='ew')
        self.frame_trackbar_gamma.grid(row=0, column=0, sticky='ew')
        self.frame_trackbar_threshold.grid(row=1, column=0, sticky='ew')

        """Layout of container"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.frame_root.grid_rowconfigure(0, weight=1)
        self.frame_root.grid_rowconfigure(1, weight=1)
        self.frame_root.grid_rowconfigure(2, weight=1)
        self.frame_root.grid_columnconfigure(0, weight=1)
        self.frame_body.grid_rowconfigure(0, weight=1)
        self.frame_body.grid_columnconfigure(0, weight=1)
        self.frame_body.grid_columnconfigure(1, weight=1)
        self.frame_panel.grid_rowconfigure(0, weight=1)
        self.frame_panel.grid_rowconfigure(1, weight=1)
        self.frame_panel.grid_columnconfigure(0, weight=1)
        self.frame_display.grid_rowconfigure(0, weight=1)
        self.frame_display.grid_rowconfigure(1, weight=1)
        self.frame_display.grid_columnconfigure(0, weight=1)
        self.frame_footer.grid_rowconfigure(0, weight=1)
        self.frame_footer.grid_rowconfigure(1, weight=1)
        self.frame_footer.grid_columnconfigure(0, weight=1)

        # Label
        from tkinter import ttk
        self._font = TkFonts()
        self.label_panel = ttk.Label(self.frame_label_panel, text='Input Panel', font=self._font.h1())
        self.label_display = ttk.Label(self.frame_label_display, text='Display', font=self._font.h1())
        self.label_panel.grid(row=0, column=0, sticky='news')
        self.label_display.grid(row=0, column=0, sticky='news')

        # Canvas
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

        self.canvas_panel = tkinter.Canvas(self.frame_canvas_panel, width=self._image_w, height=self._image_h)
        self.canvas_panel.create_image(0, 0, anchor='nw', image=self.image_panel)
        self.canvas_display = tkinter.Canvas(self.frame_canvas_display, width=self._image_w, height=self._image_h)
        self.canvas_display.create_image(0, 0, anchor='nw', image=self.image_display)

        self.canvas_panel.grid(row=0, column=0, sticky='news')
        self.canvas_display.grid(row=0, column=0, sticky='news')

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
