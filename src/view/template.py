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
from src.view.tkframe import TkFrame, TkLabelFrame
from src.view.ttkstyle import TTKStyle

LOGGER = logging.getLogger(__name__)

class MothViewerTemplate(object):

    def __init__(self):
        """
        Assume all image paths in self.image_queue are unique
        Argument:
            @image_queue        a queue of image path
            @current_image_path
            @image_panel        the image in panel
            @image_template     the template image for detection
        """
        super().__init__()
        self.image_queue = None
        self.current_image_path = None
        self.image_panel = None
        self.image_template = None
        self._font = TkFonts()

        # init windows, widget and layout
        self._init_window()
        self._init_style()
        self._init_frame()
        self._init_widget_head()
        self._init_widget_body()
        self._init_widget_footer()

    # init root window
    def _init_window(self):
        """Windows init - root"""
        self.root = tkinter.Tk()
        self.root.wm_title(time.ctime())
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    # init ttk widget style
    def _init_style(self):
        pass
    # init tk frame and grid layout
    def _init_frame(self):
        """root"""
        self.frame_root = TkFrame(self.root, bg='white')
        self.frame_root.grid(row=0, column=0)
        self.frame_root.grid_columnconfigure(0, weight=1)
        for i in range(3):
            self.frame_root.grid_rowconfigure(i, weight=1)

        """root.header"""
        self.frame_nav = TkFrame(self.frame_root, bg='orange')
        self.frame_nav.grid(row=0, column=0)

        """root.body"""
        self.frame_body = TkFrame(self.frame_root, bg='black')
        self.frame_body.grid(row=1, column=0, sticky='news')
        self.frame_body.grid_columnconfigure(0, weight=1)
        self.frame_body.grid_columnconfigure(1, weight=1)
        self.frame_body.grid_rowconfigure(0, weight=1)

        """root.body.frane_panel"""
        self.frame_panel = TkFrame(self.frame_body, bg='red')
        self.frame_panel.grid(row=0, column=0, sticky='news')
        self.frame_panel.grid_columnconfigure(0, weight=1)
        self.frame_panel.grid_rowconfigure(0, weight=1)
        self.frame_panel.grid_rowconfigure(1, weight=1)

        """root.body.frame_display"""
        self.frame_display = TkFrame(self.frame_body, bg='blue')
        self.frame_display.grid(row=0, column=1, sticky='news')
        self.frame_display.grid_columnconfigure(0, weight=1)
        self.frame_display.grid_rowconfigure(0, weight=1)
        self.frame_display.grid_rowconfigure(1, weight=1)

        """root.footer"""
        self.frame_footer = TkFrame(self.frame_root, bg='white')
        self.frame_footer.grid(row=2, column=0, sticky='news')
        self.frame_footer.grid_columnconfigure(0, weight=1)
        self.frame_footer.grid_rowconfigure(0, weight=1)
        self.frame_footer.grid_rowconfigure(1, weight=1)

        """root.footer.scalebar"""
        self.frame_scale = TkFrame(self.frame_footer, bg='orange')
        self.frame_scale.grid(row=0, column=0, sticky='news')
        self.frame_scale.grid_columnconfigure(0, weight=1)
        self.frame_scale.grid_columnconfigure(1, weight=1)
        self.frame_scale.grid_rowconfigure(0, weight=1)
        self.frame_scale.grid_rowconfigure(1, weight=1)

        """root.footer.option"""
        self.frame_option = TkLabelFrame(self.frame_footer, text='Detector', bg='light blue')
        self.frame_option.grid(row=1, column=0, sticky='news')
        self.frame_option.grid_rowconfigure(0, weight=1)

    # init header widget
    def _init_widget_head(self):
        pass

    # init body widget
    def _init_widget_body(self):
        """Panel/Display label"""
        self.label_panel = ttk.Label(self.frame_panel, text='Input Panel', font=self._font.h2())
        self.label_display = ttk.Label(self.frame_display, text='Display', font=self._font.h2())
        self.label_panel.grid(row=0, column=0)
        self.label_display.grid(row=0, column=0)

        """Panel/Display image"""
        # default output
        self._image_w, self._image_h = 800, 533
        self.photo_panel = ImageNP.generate_checkboard((self._image_h, self._image_w), block_size=10)
        self.photo_panel = TkConverter.ndarray_to_photo(self.photo_panel)
        self.photo_display = self.photo_panel

        self.label_panel_image = ttk.Label(self.frame_panel, image=self.photo_panel)
        self.label_panel_image.image = self.photo_panel
        self.label_panel_image.grid(row=1, column=0)
        self.label_display_image = ttk.Label(self.frame_display, image=self.photo_display)
        self.label_display_image.grid(row=1, column=0)

    # init footer widget
    def _init_widget_footer(self):
        """Scale bar"""
        self.label_gamma = ttk.Label(self.frame_scale, text='Gamma: ', font=self._font.h5())
        self.label_threshold = ttk.Label(self.frame_scale, text='Threshold: ', font=self._font.h5())
        self.scale_gamma = ttk.Scale(self.frame_scale,\
                                     orient=tkinter.HORIZONTAL,\
                                     length=self._image_w*2,
                                     from_=0.01, to=2.5,\
                                     variable=tkinter.DoubleVar,\
                                     value=1)
        self.scale_threshold = ttk.Scale(self.frame_scale,\
                                         orient=tkinter.HORIZONTAL,\
                                         length=self._image_w*2,\
                                         from_=1, to=255,\
                                         variable=tkinter.IntVar,\
                                         value=250)

        self.label_gamma.grid(row=0, column=0, sticky='news')
        self.scale_gamma.grid(row=0, column=1, sticky='news')
        self.label_threshold.grid(row=1, column=0, sticky='news')
        self.scale_threshold.grid(row=1, column=1, sticky='news')

    # update detector option
    def _update_detector(self):
        if self.image_template is not None:
            self.checkbtn_template_image = TkConverter.read(self.image_template)
            self.checkbtn_template = tkinter.Checkbutton(self.frame_option,
                                                         image=self.checkbtn_template_image,
                                                         font=self._font.h5(),
                                                         variable=tkinter.BooleanVar())
            self.checkbtn_template.grid(row=0, column=0)
        else:
            LOGGER.warning('No template image given')

    # inherit tkinter mainloop
    def mainloop(self):
        self._sync_image()
        self.root.mainloop()

    # input template image
    def input_template(self, template_path):
        self.image_template = template_path
        self._update_detector()

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
    TEMPLATE_IMG = abspath('../../image/10mm.png')
    SAMPLE_IMG = abspath('../../image/sample/0.jpg')

    viewer = MothViewerTemplate()
    viewer.input_template(TEMPLATE_IMG)
    viewer.input_image(SAMPLE_IMG)
    viewer.mainloop()
