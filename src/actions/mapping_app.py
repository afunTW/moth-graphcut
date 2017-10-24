"""
Defined mapping application action
"""
import logging
import os
import sys
from tkinter.filedialog import askdirectory, askopenfilename

import cv2

sys.path.append('../..')
from src.support.msg_box import MessageBox
from src.support.tkconvert import TkConverter
from src.view.mapping_app import (AutoMappingViewer, EntryMappingViewer,
                                  ManualMappingViewer)

LOGGER = logging.getLogger(__name__)

class EntryMappingAction(EntryMappingViewer):
    def __init__(self):
        super().__init__()
        self.img_path = None
        self.temp_path = None

        self.btn_img_path.config(command=self._load_img_path)
        self.btn_temp_path.config(command=self._load_temp_path)
        self.btn_ok.config(command=self._confirm)

    def _load_img_path(self):
        self.img_path = askopenfilename(
            initialdir=os.path.abspath('../../'),
            title=u'選擇原始圖片路徑',
            filetypes=(('JPG Image', '*.jpg'),('JPEG Image', '*.jpeg'))
        )
        if self.img_path:
            LOGGER.info('Original Image Path - {}'.format(self.img_path))
            self.label_img_path.config(text=self.img_path)

    def _load_temp_path(self):
        self.temp_path = askdirectory(
            initialdir=os.path.abspath('../../'),
            title=u'選擇熱像儀 (灰階) 圖片資料夾'
        )
        if self.temp_path:
            LOGGER.info('ThermalCAM gray colourmap directory - {}'.format(self.temp_path))
            self.label_temp_path.config(text=self.temp_path)

    def _confirm(self):
        if self.img_path is None:
            Mbox = MessageBox()
            Mbox.alert(title='Warning', string=u'請選擇原始圖片路徑')
        elif self.temp_path is None:
            Mbox = MessageBox()
            Mbox.alert(title='Warning', string=u'請選擇熱像儀 (灰階) 圖片資料夾')
        else:
            LOGGER.info('Ready to process')

class AutoMappingAction(AutoMappingViewer):
    def __init__(self, img_path, temp_path):
        self.img_path = img_path
        self.temp_path = temp_path

        self._original_img = None

    def _load_image(self):
        self._original_img = cv2.imread(self.img_path)
        pass

if __name__ == '__main__':
    """testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    entry_action = EntryMappingAction()
    entry_action.mainloop()
