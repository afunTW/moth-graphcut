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

import cv2
from PIL import Image, ImageTk

sys.path.append('../..')
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.actions.detector import TemplateDetector
from src.view.tkfonts import TkFonts
from src.view.tkframe import TkFrame, TkLabelFrame
from src.view.ttkstyle import TTKStyle, init_css

LOGGER = logging.getLogger(__name__)
STATE = ['view', 'erase', 'edit', 'mirror', 'seperate']

class MothViewerTemplate(object):

    def __init__(self):
        """
        Assume all image paths in self.image_queue are unique
        Argument:
            @current_image_path
            @image_queue        a queue of image path
            @image_panel        the image in panel before edit mode
            @image_panel_tmp    the image in panel after edit mode
            @image_path_template
            @image_template     the template image for detection
            @detector           a TemplateDetector() instance or None
            @state              corresponding message with application state
            @root_state         application state
            @panel_image_state  panel image state

            @symmetric_line     mirror line for moth
        """
        super().__init__()
        self.current_image_path = None
        self.image_queue = None
        self.image_panel = None
        self.image_panel_tmp = None
        self.image_path_template = None
        self.image_template = None
        self.detector = None
        self.state_message = None
        self.root_state = []
        self.panel_image_state = []

        self._font = TkFonts()

        # meta data
        self.symmetric_line = None

        # init windows, widget and layout
        self._init_window()
        self._init_style()
        self._init_frame()
        self._init_widget_head()
        self._init_widget_body()
        self._init_widget_footer()

    # set grid all column configure
    def _set_all_grid_columnconfigure(self, widget, *cols):
        for col in cols:
            widget.grid_columnconfigure(col, weight=1)

    # set grid all row comfigure
    def _set_all_grid_rowconfigure(self, widget, *rows):
        for row in rows:
            widget.grid_rowconfigure(row, weight=1)

    # init all state when image changed
    def _init_state(self):
        self.state_message = 'view'
        self.root_state = ['view']
        self.panel_image_state = []
        self._init_detector()

    # init root window
    def _init_window(self):
        """Windows init - root"""
        self.root = tkinter.Tk()
        self.root.wm_title(time.ctime())
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.attributes('-zoomed', True)

    # init ttk widget style
    def _init_style(self):
        init_css()

    # init tk frame and grid layout
    def _init_frame(self):
        """root"""
        self.frame_root = TkFrame(self.root, bg='white')
        self.frame_root.grid(row=0, column=0)
        self._set_all_grid_columnconfigure(self.frame_root, 0)
        self._set_all_grid_rowconfigure(self.frame_root, 0, 1, 2)

        """root.header"""
        self.frame_nav = TkFrame(self.frame_root, bg='orange')
        self.frame_nav.grid(row=0, column=0, sticky='news')

        """root.body"""
        self.frame_body = TkFrame(self.frame_root, bg='black')
        self.frame_body.grid(row=1, column=0, sticky='news')
        self._set_all_grid_columnconfigure(self.frame_body, 0, 1)
        self._set_all_grid_rowconfigure(self.frame_body, 0)

        """root.body.frame_panel"""
        self.frame_panel = TkFrame(self.frame_body, bg='light pink')
        self.frame_panel.grid(row=0, column=0, sticky='news')
        self._set_all_grid_columnconfigure(self.frame_panel, 0)
        self._set_all_grid_rowconfigure(self.frame_panel, 0, 1)

        """root.body.frame_display"""
        self.frame_display = TkFrame(self.frame_body, bg='royal blue')
        self.frame_display.grid(row=0, column=1, sticky='news')
        self._set_all_grid_columnconfigure(self.frame_display, 0)
        self._set_all_grid_rowconfigure(self.frame_display, 0, 1)

        """root.footer"""
        self.frame_footer = TkFrame(self.frame_root, bg='khaki1')
        self.frame_footer.grid(row=2, column=0, sticky='news')
        self._set_all_grid_columnconfigure(self.frame_footer, 0)
        self._set_all_grid_rowconfigure(self.frame_footer, 0, 1)

        """root.footer.input_option"""
        self.frame_input_option = TkLabelFrame(self.frame_footer, text=u'Input 調整參數', font=self._font.h4(), bg='gray86')
        self.frame_input_option.grid(row=0, column=0, sticky='news')
        self._set_all_grid_columnconfigure(self.frame_input_option, 0)
        self._set_all_grid_rowconfigure(self.frame_input_option, 0, 1)

        """root.footer.input_option.detect_options"""
        self.frame_detect_options = TkFrame(self.frame_input_option, padx=0, pady=0)
        self.frame_detect_options.grid(row=0, column=1, sticky='news')

        """root.footer.output_option"""
        self.frame_output_option = TkLabelFrame(self.frame_footer, text=u'Output 調整參數', font=self._font.h4(), bg='gray86')
        self.frame_output_option.grid(row=1, column=0, sticky='news')
        self._set_all_grid_columnconfigure(self.frame_output_option, 0)
        self._set_all_grid_rowconfigure(self.frame_output_option, 0)

    # init header widget
    def _init_widget_head(self):
        """State"""
        self.label_state = ttk.Label(self.frame_nav, text='', style='H1.TLabel')
        self.label_state.grid(row=0, column=0, sticky='w')
        self._sync_state()

    # init body widget
    def _init_widget_body(self):
        """Panel/Display label"""
        self.label_panel = ttk.Label(self.frame_panel, text='Input Panel', style='H2.TLabel')
        self.label_display = ttk.Label(self.frame_display, text='Display', style='H2.TLabel')
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
        self.label_panel_image.grid(row=2, column=0)
        self.label_display_image = ttk.Label(self.frame_display, image=self.photo_display)
        self.label_display_image.grid(row=2, column=0)

    # init footer widget
    def _init_widget_footer(self):
        """Input option"""
        # detector
        self.label_detector = ttk.Label(self.frame_input_option, text=u'偵測設定: ', style='H5.TLabel')
        self.label_detector.grid(row=0, column=0, sticky='w')
        self.val_manual_detect = tkinter.BooleanVar()
        self.val_template_detect = tkinter.BooleanVar()
        self.val_manual_detect.set(False)
        self.val_template_detect.set(False)
        self.checkbtn_manual_detect = ttk.Checkbutton(self.frame_detect_options,
                                                      text=u'手動清除',
                                                      style='H5.TCheckbutton',
                                                      variable=self.val_manual_detect)
        self.checkbtn_template_detect = ttk.Checkbutton(self.frame_detect_options,
                                                        text=u'自動清除',
                                                        style='H5.TCheckbutton',
                                                        variable=self.val_template_detect)
        self.checkbtn_template_detect.configure(state='disabled')
        self.checkbtn_manual_detect.grid(row=0, column=0, sticky='w')
        self.checkbtn_template_detect.grid(row=0, column=1, sticky='w')

        # scale bar
        self.label_gamma = ttk.Label(self.frame_input_option, text=u'圖片對比: ', style='H5.TLabel')
        self.val_gamma = tkinter.DoubleVar()
        self.val_gamma.set(1.0)
        self.scale_gamma = ttk.Scale(self.frame_input_option,
                                     orient=tkinter.HORIZONTAL,
                                     length=self._image_w*2,
                                     from_=0.01, to=2.5,
                                     variable=self.val_gamma,
                                     style='White.Horizontal.TScale')
        self.label_gamma.grid(row=1, column=0, sticky='news')
        self.scale_gamma.grid(row=1, column=1, sticky='news')

        """Output option"""
        # scale bar
        self.label_threshold = ttk.Label(self.frame_output_option, text=u'門檻值: ', style='H5.TLabel')
        self.val_threshold = tkinter.IntVar()
        self.val_threshold.set(250)
        self.scale_threshold = ttk.Scale(self.frame_output_option,
                                         orient=tkinter.HORIZONTAL,
                                         length=self._image_w*2,
                                         from_=1, to=255,
                                         variable=self.val_threshold,
                                         style='White.Horizontal.TScale')
        self.label_threshold.grid(row=0, column=0, sticky='news')
        self.scale_threshold.grid(row=0, column=1, sticky='news')

    # init detector
    def _init_detector(self):
        self.detector = TemplateDetector(self.image_path_template,
                                         self.current_image_path)

    # update detector option
    def _enable_detector(self):
        if self.image_path_template is not None:
            self.image_template = cv2.imread(self.image_path_template)
            self.checkbtn_template_detect.configure(state='normal')
            self.val_template_detect.set(True)
        else:
            LOGGER.warning('No template image given')

    # read a new image and update to panel
    def _update_image(self, image_path=None, edit_mode=False):
        if image_path is not None:
            try:
                self.photo_panel = tkinter.PhotoImage(file=image_path)
                self._image_w, self._image_h = self.photo_panel.width(), self.photo_panel.height()
            except tkinter.TclError as loaderr:
                # log level should be warning in this block
                LOGGER.debug(loaderr)
                self.image_panel = cv2.imread(image_path)
                self._image_h, self._image_w, _ = self.image_panel.shape
                self.photo_panel = TkConverter.cv2_to_photo(self.image_panel)
            except Exception as e:
                LOGGER.exception(e)
            self.current_image_path = image_path
        elif edit_mode:
            self.photo_panel = TkConverter.cv2_to_photo(self.image_panel_tmp)
        else:
            self.photo_panel = TkConverter.cv2_to_photo(self.image_panel)

    # render the lastest panel image
    def _sync_image(self):
        self.root.wm_title(self.current_image_path)
        self.label_panel_image.config(image=self.photo_panel)
        self.label_panel_image.after(100, self._sync_image)

    # render the lastest state
    def _sync_state(self):
        msg = ''
        if self.state_message not in STATE:
            msg = u'無'
        elif self.state_message == 'view':
            msg = u'瀏覽 (按下 ENTER 進入編輯模式)'
        elif self.state_message == 'erase':
            msg = u'手動消除 (按下 ENTER 進入編輯模式)'
        elif self.state_message == 'edit':
            msg = u'編輯'
        elif self.state_message == 'mirror':
            msg = u'鏡像'
        elif self.state_message == 'seperate':
            msg = u'切割'
        self.label_state.configure(text=u'現在模式: {}'.format(msg))
        self.label_state.after(100, self._sync_state)

    # input template image
    def input_template(self, template_path):
        self.image_path_template = template_path
        self._enable_detector()

    # input all image path to queue
    def input_image(self, *image_paths):
        self.image_queue = image_paths
        self._update_image(self.image_queue[0])

    # inherit tkinter mainloop
    def mainloop(self):
        self._sync_image()
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
    TEMPLATE_IMG = abspath('../../image/10mm.png')
    SAMPLE_IMG = abspath('../../image/sample/0.jpg')

    viewer = MothViewerTemplate()
    viewer.input_template(TEMPLATE_IMG)
    viewer.input_image(SAMPLE_IMG)
    viewer.mainloop()
