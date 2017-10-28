import json
import logging
import os
import sys
import tkinter
from inspect import currentframe, getframeinfo
from tkinter import ttk
sys.path.append('../..')

import cv2
from src.view.template import ImageViewer, TkViewer
from src.view.tkframe import TkFrame
from src.view.ttkstyle import TTKStyle, init_css

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)
OUTFILE_TYPE = [('.dat', 'ndarray'), ('.txt', 'text')]


class EntryThermalComponentViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._init_window(zoom=False)
        self._init_frame()
        self._init_style()

    # init tk frame and layout
    def _init_frame(self):
        # root
        self.frame_root = TkFrame(self.root)
        self.frame_root.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_root, 0)
        self.set_all_grid_columnconfigure(self.frame_root, 0)

        # body
        self.frame_body = TkFrame(self.frame_root)
        self.frame_body.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_body, 0, 1, 2)
        self.set_all_grid_columnconfigure(self.frame_body, 0)

        # body > option
        self.frame_option = TkFrame(self.frame_body)
        self.frame_option.grid(row=0, column=0, sticky='w')
        self.set_all_grid_rowconfigure(self.frame_option, 0)
        self.set_all_grid_columnconfigure(self.frame_option, *[i for i in range(len(OUTFILE_TYPE)+1)])

        # body > upload
        self.frame_upload = TkFrame(self.frame_body)
        self.frame_upload.grid(row=1, column=0, sticky='w')
        self.set_all_grid_rowconfigure(self.frame_upload, 0, 1, 2, 3)
        self.set_all_grid_columnconfigure(self.frame_upload, 0, 1, 2)

        # body > btn
        self.frame_btn = TkFrame(self.frame_body)
        self.frame_btn.grid(row=2, column=0, sticky='e')
        self.set_all_grid_rowconfigure(self.frame_btn, 0)
        self.set_all_grid_columnconfigure(self.frame_btn, 0)

        self._init_widget_body()

    # init ttk style
    def _init_style(self):
        init_css()
        TTKStyle('H5Bold.TLabel', font=('', 13))
        TTKStyle('Title.TLabel', font=('', 13, 'bold'))
        TTKStyle('H5.TLabel', font=('', 13))
        TTKStyle('H5.TButton', font=('', 13))
        TTKStyle('H5.TRadiobutton', font=('', 13))

    # init ttk widget
    def _init_widget_body(self):
        # option
        self.label_option = ttk.Label(self.frame_option, text=u'輸出檔案類型: ', style='Title.TLabel')
        self.label_option.grid(row=0, column=0, sticky='w')
        self.val_filetype = tkinter.StringVar()
        self.val_filetype.set('ndarray')
        self.radiobtn = []
        for i, filetype in enumerate(OUTFILE_TYPE):
            text, mode = filetype
            radiobtn = ttk.Radiobutton(self.frame_option, text=text, variable=self.val_filetype, value=mode, style='H5.TRadiobutton')
            radiobtn.grid(row=0, column=i+1, sticky='w')
            self.radiobtn.append(radiobtn)

        # upload: thermal txt directory
        self.label_thermal_txt = ttk.Label(self.frame_upload, text=u'溫度檔資料夾 ', style='Title.TLabel')
        self.label_thermal_txt.grid(row=0, column=0, sticky='w')
        self.btn_thermal_txt_upload = ttk.Button(self.frame_upload, text=u'上傳', style='H5.TButton')
        self.btn_thermal_txt_upload.grid(row=0, column=1, sticky='w')

        # upload: transform matrix
        self.label_transform_matrix = ttk.Label(self.frame_upload, text=u'轉換矩陣 ', style='Title.TLabel')
        self.label_transform_matrix.grid(row=1, column=0, sticky='w')
        self.btn_transform_matrix_upload = ttk.Button(self.frame_upload, text=u'上傳', style='H5.TButton')
        self.btn_transform_matrix_upload.grid(row=1, column=1, sticky='w')

        # upload: contour
        self.label_contour_meta = ttk.Label(self.frame_upload, text=u'輪廓資訊 ', style='Title.TLabel')
        self.label_contour_meta.grid(row=2, column=0, sticky='w')
        self.btn_contour_meta_upload = ttk.Button(self.frame_upload, text=u'上傳', style='H5.TButton')
        self.btn_contour_meta_upload.grid(row=2, column=1, sticky='w')

        # upload: output path
        self.label_output_path = ttk.Label(self.frame_upload, text=u'輸出路徑', style='Title.TLabel')
        self.label_output_path.grid(row=3, column=0, sticky='w')

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    entry = EntryThermalComponentViewer()
    entry.mainloop()
