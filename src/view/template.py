"""
Wrap the tkinter function for this project
"""
import inspect
import logging
import os
import sys
import time
import tkinter
from inspect import currentframe, getframeinfo
from tkinter import ttk
from tkinter.filedialog import askopenfilenames

import cv2
from PIL import Image, ImageTk

sys.path.append('../..')
from src.actions.detector import TemplateDetector
from src.image.imcv import ImageCV
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.tkfonts import TkFonts
from src.view.tkframe import TkFrame, TkLabelFrame
from src.view.ttkstyle import TTKStyle, init_css

__FILE__ = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
LOGGER = logging.getLogger(__name__)
STATE = ['view', 'erase', 'edit', 'mirror', 'seperate', 'calc', 'result']

# the basic template for image application
class ImageViewer(object):
    """
    Assume all image paths in self.image_queue are unique,
    show the image on ttk.Label named panel and sync the image to photo

    Argument:
        @current_image_path
        @image_queue        a queue of image path
        @image_panel        a image ready to display on panel
        @photo_panel        a photo to display on ttk widget (label)
        @photo_display      a photo to display on ttk widget (label)
        @state_message      corresponding message with application state
        @root_state         application state
    """
    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.image_queue = None
        self.image_panel = None
        self.photo_panel = None
        self.photo_display = None
        self.state_message = None
        self.root_state = []

        # ready to deprecated for tk widget, using ttk style after new version
        self._font = TkFonts()

    # set grid all column configure
    def _set_all_grid_columnconfigure(self, widget, *cols):
        for col in cols:
            widget.grid_columnconfigure(col, weight=1)

    # set grid all row comfigure
    def _set_all_grid_rowconfigure(self, widget, *rows):
        for row in rows:
            widget.grid_rowconfigure(row, weight=1)

    # init root window
    def _init_window(self, zoom=True):
        """Windows init - root"""
        try:
            self.root = tkinter.Tk()
            self.root.wm_title(time.ctime())
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)
            if os.name == 'posix':
                self.root.attributes('-zoomed', zoom)
            elif os.name == 'wt':
                self.root.state('zoomed')
            else:
                LOGGER.warning('Your platform {} does not support zooming in this app'.format(
                    os.name
                ))
        except Exception as e:
            LOGGER.exception(e)

    # init ttk widget style
    def _init_style(self):
        init_css()

    # init all state when image changed
    def _init_state(self):
        self.root_state = ['view']
        self.state_message = 'view'

    # render the lastest panel image
    def _sync_image(self):
        pass

    # render the lastest display changed
    def _sync_display(self):
        pass

    # read a new image and update to panel
    def _update_image(self, image_path=None, image=None):
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
            current_index = self.image_queue.index(self.current_image_path)+1
            LOGGER.info('({}/{}) Ready to process image {}'.format(
                current_index, len(self.image_queue), self.current_image_path
            ))
        elif image is not None:
            try:
                self.photo_panel = TkConverter.cv2_to_photo(image)
            except Exception as e:
                LOGGER.exception(e)
        else:
            self.photo_panel = TkConverter.cv2_to_photo(self.image_panel)

        self._image_h, self._image_w = self.image_panel.shape[0], self.image_panel.shape[1]

    # update the display photo accroding to image operation in panel
    def _update_display(self, image):
        try:
            self.photo_display = TkConverter.cv2_to_photo(image)
        except Exception as e:
            h, w, _ = self.image_panel.shape
            error_display = ImageNP.generate_checkboard((h, w), block_size=10)
            error_display = ImageCV.generate_error_mask(error_display)
            self.photo_display = TkConverter.cv2_to_photo(error_display)
            LOGGER.exception(e)

    # unique the list element
    def unique(self, l):
        return list(set(l))

    # input all image path to queue
    def input_image(self, *image_paths):
        self.image_queue = image_paths
        self._update_image(self.image_queue[0])

    # inherit tkinter mainloop
    def mainloop(self):
        self.root.mainloop()

# the interface to preprocess moth image
class PreprocessViewer(ImageViewer):
    def __init__(self):
        super().__init__()
        self._image_original = None
        self._image_w, self._image_h = 800, 533

        self._init_window(zoom=False)
        self.root.option_add('*tearOff', False)
        self._init_style()
        self._init_frame()
        self._init_menu_bar()
        self._init_widget_head()
        self._init_widget_body()
        self._init_widget_footer()
        self._init_state()

    # init all state when image changed
    def _init_state(self):
        self.state_message = 'view'
        self.root_state = ['view']
        self._init_floodfill_option()
        self._init_display_panel()

    # init menu to load image path
    def _init_menu_bar(self):
        self.root_menu = tkinter.Menu(self.root)
        self.root.config(menu=self.root_menu)

        self.menu_image = tkinter.Menu(self.root_menu)
        self.menu_image.add_command(label=u'載入圖片', command=self.get_image_queue)

        self.root_menu.add_cascade(label='File', menu=self.menu_image)

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

        """root.footer.floodfill"""
        self.frame_floodfill = TkLabelFrame(self.frame_footer, text=u'Flood Fill 演算法參數', font=self._font.h4())
        self.frame_floodfill.grid(row=0, column=0, sticky='news')
        self._set_all_grid_columnconfigure(self.frame_floodfill, 0)
        self._set_all_grid_rowconfigure(self.frame_floodfill, 0, 1)

    # init header widget
    def _init_widget_head(self):
        """Resize state"""
        self.label_state = ttk.Label(self.frame_nav, text='', style='H2.TLabel')
        self.label_resize = ttk.Label(self.frame_nav, text=u'顯示尺寸: ', style='H2.TLabel')
        self.label_state.grid(row=0, column=0, sticky='w')
        self.label_resize.grid(row=1, column=0, sticky='w')
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
        """Flood fill algorithm threshold (Double)"""
        self.label_floodfill_threshold = ttk.Label(self.frame_floodfill, text=u'門檻值: ', style='H5.TLabel')
        self.val_scale_threshold = tkinter.DoubleVar()
        self.val_scale_threshold.set(0.85)
        self.scale_threshold = ttk.Scale(self.frame_floodfill,
                                         orient=tkinter.HORIZONTAL,
                                         length=self._image_w*2,
                                         from_=0.01, to=0.99,
                                         variable=self.val_scale_threshold,
                                         style='White.Horizontal.TScale')

        self.label_floodfill_threshold.grid(row=0, column=0, sticky='w')
        self.scale_threshold.grid(row=0, column=1, sticky='w')

        """Flood fill algorithm iteration (Int)"""
        self.label_floodfill_iter = ttk.Label(self.frame_floodfill, text=u'迭代次數: ', style='H5.TLabel')
        self.val_scale_iter = tkinter.IntVar()
        self.val_scale_iter.set(5)
        self.scale_iter = ttk.Scale(self.frame_floodfill,
                                    orient=tkinter.HORIZONTAL,
                                    length=self._image_w*2,
                                    from_=1, to=10,
                                    variable=self.val_scale_iter,
                                    style='White.Horizontal.TScale')

        self.label_floodfill_iter.grid(row=1, column=0, sticky='w')
        self.scale_iter.grid(row=1, column=1, sticky='w')

    # init display panel
    def _init_display_panel(self):
        resize_display = ImageNP.generate_checkboard((self._image_h, self._image_w), block_size=10)
        self.photo_display = TkConverter.ndarray_to_photo(resize_display)
        self._sync_display()

    # init floodfill option
    def _init_floodfill_option(self):
        self.val_scale_threshold.set(0.85)
        self.val_scale_iter.set(5)

    # render the lastest panel image
    def _sync_image(self):
        self.root.wm_title(self.current_image_path)
        self.root.update()
        if self.current_image_path is not None:
            self._sync_size_msg()
            self.label_panel_image.config(image=self.photo_panel)
            self.label_panel_image.after(10, self._sync_image)

    # render the lastest display changed
    def _sync_display(self):
        self.label_display_image.config(image=self.photo_display)
        self.label_display_image.after(10, self._sync_display)

    # render the lastest state
    def _sync_state(self):
        msg = ''
        if self.state_message not in STATE:
            msg = u'無'
        elif self.state_message == 'view':
            msg = u'瀏覽 (按下 ENTER 進入編輯模式)'
        elif self.state_message == 'edit':
            msg = u'編輯'
        elif self.state_message == 'calc':
            LOGGER.info('root state {}'.format(self.root_state))
            msg = u'圖片處理中...'

        if 'result' in self.root_state and self.state_message != 'calc':
            msg += ' (按下 SPACE 儲存圖片)'
        self.root_state = self.unique(self.root_state)
        self.label_state.configure(text=u'現在模式: {}'.format(msg))
        self.label_state.after(10, self._sync_state)

    # render the image size image
    def _sync_size_msg(self):
        orig_h, orig_w, orig_channel = self._image_original.shape
        resize_h, resize_w, resiez_channel = self.image_panel.shape
        msg= u'顯示尺寸: {}x{} (原始尺寸 {}x{})'.format(
            resize_w, resize_h, orig_w, orig_h
        )
        self.label_resize.configure(text=msg)

    # update and auto resize the image if read the first image
    def _update_image(self, image_path=None, image=None):
        if image_path is not None:
            try:
                self.image_panel = cv2.imread(image_path)
                self._image_original = self.image_panel.copy()
                self.image_panel = self.auto_resize(self.image_panel, ratio=0.45)
                self._image_h, self._image_w, _ = self.image_panel.shape
                self.photo_panel = TkConverter.cv2_to_photo(self.image_panel)
            except tkinter.TclError as loaderr:
                LOGGER.exception(loaderr)
            except Exception as e:
                LOGGER.exception(e)
            self.current_image_path = image_path
            current_index = self.image_queue.index(self.current_image_path)+1
            LOGGER.info('({}/{}) Ready to process image {}'.format(
                current_index, len(self.image_queue), self.current_image_path
            ))
        else:
            super()._update_image(image_path=image_path, image=image)

    # input all image path to queue
    def input_image(self, *image_paths):
        super().input_image(*image_paths)
        self._init_display_panel()

    # auto fit the image hight from original image to resize image
    def auto_resize(self, image, ratio=0.5):
        screen_h = self.root.winfo_screenheight()
        screen_w = self.root.winfo_screenwidth()
        image_h, image_w, image_channel = image.shape
        resize_h = screen_h*ratio
        resize_w = (resize_h/image_h)*image_w
        resize_h, resize_w = int(resize_h), int(resize_w)
        image = cv2.resize(image, (resize_w, resize_h), interpolation=cv2.INTER_AREA)
        LOGGER.info('resize image from {}x{} to {}x{}'.format(
            image_w, image_h, int(resize_w), int(resize_h)
        ))
        return image

    # open a file dialog to get image queue
    def get_image_queue(self):
        init_dir = os.path.abspath(os.path.join(__FILE__, '../../../image/thermal/original_rgb'))
        LOGGER.info(init_dir)
        paths = askopenfilenames(title=u'請選擇要處理的圖片',
                                 filetypes=[('JPG file (*.jpg)', '*jpg'),
                                            ('JPEG file (*.jpeg)', '*.jpeg'),
                                            ('PNG file (*.png)', '*.png')],
                                initialdir=init_dir,
                                parent=self.root)
        if paths:
            self.input_image(*paths)
            self._init_state()

    # inherit parent mainloop
    def mainloop(self):
        self._sync_image()
        super().mainloop()

# the interface to graphcut moth
class GraphcutViewer(ImageViewer):
    """
    Assume all image paths in self.image_queue are unique
    Argument:
        @image_panel        the image in panel before edit mode
        @image_panel_tmp    the image in panel after edit mode
        @image_path_template
        @image_template     the template image for detection
        @detector           a TemplateDetector() instance or None
        @panel_image_state  panel image state

        @symmetric_line     mirror line for moth
        @body_width         body width of moth
    """
    def __init__(self):
        super().__init__()
        self.image_panel_tmp = []
        self.image_path_template = None
        self.image_template = None
        self.detector = None
        self.panel_image_state = []

        # meta data
        self.symmetric_line = None
        self.body_width = None

        # init windows, widget and layout
        self._init_window()
        self._init_style()
        self._init_frame()
        self._init_widget_head()
        self._init_widget_body()
        self._init_widget_footer()

    # return the latest panel image in edit mode
    @property
    def latest_image_panel(self):
        if self.image_panel_tmp:
            return self.image_panel_tmp[-1]
        else:
            LOGGER.warning('image_panel_tmp = {}, current app state = {}'.format(
                self.image_panel_tmp, self.root_state
            ))

    # return left bounding line with moth body width
    @property
    def body_bound_line_left(self):
        if self.symmetric_line is not None and self.body_width is not None:
            pt1, pt2 = self.symmetric_line
            bound_x = max(pt1[0]-self.body_width, 0)
            bound_pt1 = (bound_x, pt1[1])
            bound_pt2 = (bound_x, pt2[1])
            return (bound_pt1, bound_pt2)
        else:
            LOGGER.warning('symmetric_line = {}, body_width = {}'.format(
                self.symmetric_line, self.body_width
            ))

    # return right bounding line with moth body width
    @property
    def body_bound_line_right(self):
        if self.symmetric_line is not None and self.body_width is not None:
            pt1, pt2 = self.symmetric_line
            h, w, _ = self.image_panel.shape
            bound_x = min(pt1[0]+self.body_width, w)
            bound_pt1 = (bound_x, pt1[1])
            bound_pt2 = (bound_x, pt2[1])
            return (bound_pt1, bound_pt2)
        else:
            LOGGER.warning('symmetric_line = {}, body_width = {}'.format(
                self.symmetric_line, self.body_width
            ))

    # init all state when image changed
    def _init_state(self):
        self.state_message = 'view'
        self.root_state = ['view']
        self.panel_image_state = []
        self.image_panel_tmp = []
        self._init_detector()
        self._enable_detector()

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
        self.checkbtn_manual_detect.configure(state='normal')
        if self.image_path_template is not None:
            self.image_template = cv2.imread(self.image_path_template)
            self.checkbtn_template_detect.configure(state='normal')
            self.val_manual_detect.set(False)
            self.val_template_detect.set(True)
        else:
            LOGGER.warning('No template image given')

    # render the lastest panel image
    def _sync_image(self):
        self.root.wm_title(self.current_image_path)
        self.root.update()
        self._draw()
        self.label_panel_image.config(image=self.photo_panel)
        self.label_panel_image.after(10, self._sync_image)

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
        self.label_state.after(10, self._sync_state)

    # draw meta data on image panel
    def _draw(self):
        if self.image_panel_tmp:
            render_image = self.latest_image_panel.copy()

            if 'edit' in self.root_state:
                if self.symmetric_line:
                    pt1, pt2 = self.symmetric_line
                    cv2.line(render_image, pt1, pt2, (0, 0, 0), 2)

            if 'mirror' in self.root_state:
                if self.body_width:
                    l_pt1, l_pt2 = self.body_bound_line_left
                    r_pt1, r_pt2 = self.body_bound_line_right
                    cv2.line(render_image, l_pt1, l_pt2, (255, 0, 0), 2)
                    cv2.line(render_image, r_pt1, r_pt2, (255, 0, 0), 2)

            self._update_image(image=render_image)

    # input all image path to queue
    def input_image(self, *image_paths):
        super().input_image(*image_paths)
        self._init_state()

    # input template image
    def input_template(self, template_path):
        self.image_path_template = template_path
        self._enable_detector()

    # inherit parent mainloop
    def mainloop(self):
        self._sync_image()
        super().mainloop()

if __name__ == '__main__':
    """testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
    _FILE = os.path.abspath(getframeinfo(currentframe()).filename)
    TEMPLATE_IMG = os.path.abspath('../../image/10mm.png')
    SAMPLE_IMG = os.path.abspath('../../image/sample/0.jpg')
    THERMAL_IMG = os.path.abspath('../../image/thermal/original_rgb/_SWU9909.jpg')

    import os
    if not os.path.exists(THERMAL_IMG):
        import zipfile
        with zipfile.ZipFile(os.path.abspath('../../image/thermal.zip'), 'r') as zip_ref:
            zip_ref.extractall(os.path.abspath('../../image'))

    preprocess_viewer = PreprocessViewer()
    preprocess_viewer.input_image(THERMAL_IMG)
    preprocess_viewer.mainloop()

    # graphcut_viewer = GraphcutViewer()
    # graphcut_viewer.input_template(TEMPLATE_IMG)
    # graphcut_viewer.input_image(SAMPLE_IMG)
    # graphcut_viewer.mainloop()
