"""
Wrap the tkinter function for this project
"""
import logging
import sys
import time
import tkinter
from inspect import currentframe, getframeinfo
from os.path import abspath
from tkinter import ttk

from PIL import Image, ImageTk

sys.path.append('../..')
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.tkfonts import TkFonts
from src.view.tkframe import TkFrame

LOGGER = logging.getLogger(__name__)

class MothViewerTemplate(object):

    def __init__(self):
        '''
        Assume all image paths in self.image_queue are unique
        '''
        super().__init__()
        self.root = tkinter.Tk()
        self.root.wm_title(time.ctime())
        self.image_queue = None
        self.current_image_path = None

        '''Frame init'''
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

        '''Widget manager'''
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

        '''Layout of container'''
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        '''Label'''
        self._font = TkFonts()
        self.label_panel = ttk.Label(self.frame_label_panel_text, text='Input Panel', font=self._font.h2())
        self.label_display = ttk.Label(self.frame_label_display_text, text='Display', font=self._font.h2())
        self.label_panel.grid(sticky='news')
        self.label_display.grid(sticky='news')

        '''Canvas'''
        # default output
        self._image_w, self._image_h = 800, 533
        self.photo_display = ImageNP.generate_checkboard((self._image_h, self._image_w), block_size=10)
        self.photo_display = TkConverter.ndarray_to_photo(self.photo_display)
        self.photo_panel = self.photo_display

        self.label_panel_image = ttk.Label(self.frame_label_panel_image, image=self.photo_panel)
        self.label_panel_image.grid(row=0, column=0, sticky='news')
        self.label_display_image = ttk.Label(self.frame_label_display_image, image=self.photo_display)
        self.label_display_image.grid(row=0, column=0, sticky='news')


    def mainloop(self):
        self._sync_image()
        self.root.mainloop()

    # input all image path to queue
    def input_image(self, *image_paths):
        self.image_queue = image_paths
        self._update_image(self.image_queue[0])

    # read a new image and update to panel
    def _update_image(self, image_path=None):
        if image_path is not None:
            try:
                self.photo_panel = tkinter.PhotoImage(file=image_path)
                self._image_w, self._image_h = self.photo_panel.width(), self.photo_panel.height()
            except tkinter.TclError as loaderr:
                # log level should be warning in this block
                LOGGER.debug(loaderr)
                self.image_panel = Image.open(image_path)
                self._image_h, self._image_w = self.image_panel.size
                self.photo_panel = ImageTk.PhotoImage(self.image_panel)
            except Exception as e:
                LOGGER.exception(e)
            self.current_image_path = image_path
            # self._sync_image()
        else:
            LOGGER.warning('No image_path')

    # render the lastest panel image
    def _sync_image(self):
        self.root.wm_title(self.current_image_path)
        self.label_panel_image.config(image=self.photo_panel)
        self.label_panel_image.after(100, self._sync_image)

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

    viewer = MothViewerTemplate()
    # viewer._update_image(SAMPLE_IMG)
    viewer.mainloop()
