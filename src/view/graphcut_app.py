import logging
import os
import sys
import tkinter
from tkinter import ttk
sys.path.append('../..')

import cv2
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.template import TkViewer
from src.view.tkfonts import TkFonts
from src.view.tkframe import TkFrame, TkLabelFrame
from src.view.ttkstyle import TTKStyle, init_css

LOGGER = logging.getLogger(__name__)

class GraphCutViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._im_w, self._im_h = 800, 533
        self._init_window(zoom=False)
        self._init_style()
        self._init_frame()

    def _init_style(self):
        init_css()
        self.font = TkFonts()

    # init frame
    def _init_frame(self):
        # root
        self.frame_root = TkFrame(self.root)
        self.frame_root.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_root, 0, 1, 2)
        self.set_all_grid_columnconfigure(self.frame_root, 0)

        # head
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
        self.set_all_grid_rowconfigure(self.frame_footer, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_footer, 0)

        # footer > panel setting
        self.frame_panel_setting = TkLabelFrame(self.frame_footer, text=u'輸入圖片選項: ', font=self.font.h4())
        self.frame_panel_setting.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_panel_setting, 0)
        self.set_all_grid_columnconfigure(self.frame_panel_setting, 0)

        # footer > display setting
        self.frame_display_setting = TkLabelFrame(self.frame_footer, text=u'輸出圖片選項: ', font=self.font.h4())
        self.frame_display_setting.grid(row=1, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_display_setting, 0)
        self.set_all_grid_columnconfigure(self.frame_display_setting, 0)

        self._init_widget_head()
        self._init_widget_body()

    # init head widget
    def _init_widget_head(self):
        self.label_state = ttk.Label(self.frame_head, text=u'現在模式: N/A', style='H2.TLabel')
        self.label_state.grid(row=0, column=0, sticky='w')

    # init body widget
    def _init_widget_body(self):
        # panel
        self.set_all_grid_rowconfigure(self.frame_panel, 0, 1)
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

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    graphcut_viewer = GraphCutViewer()
    graphcut_viewer.mainloop()
