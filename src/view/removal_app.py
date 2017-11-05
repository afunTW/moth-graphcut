import logging
import os
import sys
import tkinter
from tkinter import ttk
sys.path.append('../..')

from PIL import Image

import cv2
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.template import TkViewer
from src.view.tkfonts import TkFonts
from src.view.tkframe import TkFrame, TkLabelFrame
from src.view.ttkstyle import TTKStyle, init_css


LOGGER = logging.getLogger(__name__)

class RemovalViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._im_w, self._im_h = 800, 533
        self._init_window(zoom=False)
        self._init_menu()
        self._init_style()
        self._init_frame()

    # init ttk style
    def _init_style(self):
        init_css()
        self.font = TkFonts()
        TTKStyle('H2BlackdBold.TLabel', font=('', 24, 'bold'), background='white', foreground='black')
        TTKStyle('H2RedBold.TLabel', font=('', 24, 'bold'), background='white', foreground='red')

    # init tk frame and grid layout
    def _init_frame(self):
        # root
        self.frame_root = TkFrame(self.root, bg='white')
        self.frame_root.grid(row=0, column=0)
        self.set_all_grid_rowconfigure(self.frame_root, 0, 1, 2)
        self.set_all_grid_columnconfigure(self.frame_root, 0)

        # header
        self.frame_head = TkFrame(self.frame_root, bg='white')
        self.frame_head.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_head, 0)
        self.set_all_grid_columnconfigure(self.frame_head, 0)

        # body
        self.frame_body = TkFrame(self.frame_root, bg='black')
        self.frame_body.grid(row=1, column=0, sticky='news')
        self.set_all_grid_columnconfigure(self.frame_body, 0, 1)
        self.set_all_grid_rowconfigure(self.frame_body, 0)

        # body > panel
        self.frame_panel = TkFrame(self.frame_body, bg='light pink')
        self.frame_panel.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_panel, 0)
        self.set_all_grid_columnconfigure(self.frame_panel, 0)

        # body > display
        self.frame_display = TkFrame(self.frame_body, bg='royal blue')
        self.frame_display.grid(row=0, column=1, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_display, 0)
        self.set_all_grid_columnconfigure(self.frame_display, 0)

        # footer
        self.frame_footer = TkFrame(self.frame_root, bg='gray82')
        self.frame_footer.grid(row=2, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_footer, 0)
        self.set_all_grid_columnconfigure(self.frame_footer, 0)

        # footer > floodfill
        self.frame_floodfill = TkLabelFrame(self.frame_footer, text=u'Flood Fill 演算法參數', font=self.font.h4())
        self.frame_floodfill.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_floodfill, 0)
        self.set_all_grid_columnconfigure(self.frame_floodfill, 0)

        self._init_widget_head()
        self._init_widget_body()
        self._init_widget_footer()

    # init header widget
    def _init_widget_head(self):
        # resize
        self.set_all_grid_rowconfigure(self.frame_head, 0, 1)
        self.label_state = ttk.Label(self.frame_head, text=u'現在模式: N/A', style='H2.TLabel')
        self.label_state.grid(row=0, column=0, sticky='w')
        self.label_resize = ttk.Label(self.frame_head, text=u'原有尺寸 N/A-> 顯示尺寸 N/A', style='H2.TLabel')
        self.label_resize.grid(row=1, column=0, sticky='w')

    # init body widget
    def _init_widget_body(self):
        # panel
        # self.set_all_grid_rowconfigure(self.frame_panel, 0, 1)
        self.label_panel = ttk.Label(self.frame_panel, text='Input Panel', style='H2.TLabel')
        self.label_panel.grid(row=0, column=0, sticky='ns')
        self.photo_panel = ImageNP.generate_checkboard((self._im_h, self._im_w), block_size=10)
        self.photo_panel = TkConverter.ndarray_to_photo(self.photo_panel)
        self.label_panel_image = ttk.Label(self.frame_panel, image=self.photo_panel)
        self.label_panel_image.grid(row=1, column=0, sticky='ns')

        # display
        self.label_display = ttk.Label(self.frame_display, text='Display', style='H2.TLabel')
        self.label_display.grid(row=0, column=0, sticky='ns')
        self.photo_display = self.photo_panel
        self.label_display_image = ttk.Label(self.frame_display, image=self.photo_display)
        self.label_display_image.grid(row=1, column=0, sticky='ns')

    # init footer widget
    def _init_widget_footer(self):
        self.set_all_grid_rowconfigure(self.frame_floodfill, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_floodfill, 0, 1)

        # floodfill threshold
        self.val_scale_threshold = tkinter.DoubleVar()
        self.val_scale_threshold.set(0.85)
        self.label_floodfill_threshold = ttk.Label(self.frame_floodfill, text=u'門檻值 ({:.2f}): '.format(0.85), style='H5.TLabel')
        self.scale_threshold = ttk.Scale(self.frame_floodfill,
                                         orient=tkinter.HORIZONTAL,
                                         length=self._im_w * 2,
                                         from_=0.01, to=0.99,
                                         variable=self.val_scale_threshold,
                                         style='Gray.Horizontal.TScale')
        self.label_floodfill_threshold.grid(row=0, column=0, sticky='w')
        self.scale_threshold.grid(row=0, column=1, sticky='w')

        # floodfill iteration count
        self.val_scale_iter = tkinter.DoubleVar()
        self.val_scale_iter.set(5)
        self.label_floodfill_iter = ttk.Label(self.frame_floodfill, text=u'迭代次數 ({:2.0f}): '.format(5.), style='H5.TLabel')
        self.scale_iter = ttk.Scale(self.frame_floodfill,
                                    orient=tkinter.HORIZONTAL,
                                    length=self._im_w * 2,
                                    from_=1, to=10,
                                    variable=self.val_scale_iter,
                                    style='Gray.Horizontal.TScale')
        self.label_floodfill_iter.grid(row=1, column=0, sticky='w')
        self.scale_iter.grid(row=1, column=1, sticky='w')

    # init menu bar
    def _init_menu(self):
        # root
        self.menu_root = tkinter.Menu(self.root)
        self.root.config(menu=self.menu_root)

        # load image
        self.menu_load_img = tkinter.Menu(self.menu_root)

        # show menu
        self.menu_root.add_cascade(label=u'File', menu=self.menu_load_img)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    removal_viewer = RemovalViewer()
    removal_viewer.mainloop()
