import json
import logging
import os
import sys
import tkinter
from inspect import currentframe, getframeinfo
from tkinter.filedialog import askdirectory, askopenfilename
sys.path.append('../..')

import numpy as np

from src.support.msg_box import MessageBox
from src.view.component_app import EntryThermalComponentViewer

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)

class EntryThermalComponentAction(EntryThermalComponentViewer):
    def __init__(self):
        super().__init__()
        # path
        self._thermal_dir_path = None
        self._transform_matrix_path = None
        self._contour_path = None
        self._output_dir_path = None

        # file
        self._transform_matrix = None
        self._contour_meta = None

        self.btn_thermal_txt_upload.config(command=self._load_thermal_dir)
        self.btn_transform_matrix_upload.config(command=self._load_transform_matrix)
        self.btn_contour_meta_upload.config(command=self._load_contour_path)
        self._sync_generate_save_path()

    # load thermal directory
    def _load_thermal_dir(self):
        self._thermal_dir_path = askdirectory(
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
            title=u'選擇溫度檔資料夾 (.txt)'
        )

        if self._thermal_dir_path:
            LOGGER.info('Thermal txt directory - {}'.format(self._thermal_dir_path))
            self.label_thermal_path.config(text=self._thermal_dir_path)

    # load transform matrix path
    def _load_transform_matrix(self):
        self._transform_matrix_path = askopenfilename(
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
            title=u'選擇轉換矩陣路徑',
            filetypes=(('Numpy array', '*.dat'),)
        )

        if self._transform_matrix_path:
            LOGGER.info('Transform matrix file - {}'.format(self._transform_matrix_path))
            self.label_transform_matrix_path.config(text=self._transform_matrix_path)
            self._transform_matrix = np.fromfile(self._transform_matrix_path)

    # load contour metadata path
    def _load_contour_path(self):
        self._contour_path = askopenfilename(
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
            title=u'選擇輪廓資訊路徑',
            filetypes=(('JSON file', '*.json'),)
        )

        if self._contour_path:
            LOGGER.info('Contour meta - {}'.format(self._contour_path))
            self.label_contour_meta_path.config(text=self._contour_path)
            with open(self._contour_path, 'r') as f:
                self._contour_meta = json.load(f)

    # sync save path
    def _sync_generate_save_path(self):
        if self._thermal_dir_path and self.val_filetype.get():
            self._output_dir_path = '{}_warp_{}'.format(self._thermal_dir_path, self.val_filetype.get())
            self.label_output_path.config(text=self._output_dir_path)

        self.label_output_path.after(10, self._sync_generate_save_path)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    entry = EntryThermalComponentAction()
    entry.mainloop()
