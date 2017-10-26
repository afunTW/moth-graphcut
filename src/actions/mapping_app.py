"""
Defined mapping application action
"""
import logging
import os
import sys
from tkinter.filedialog import askdirectory, askopenfilename

import cv2

sys.path.append('../..')
from src.actions.alignment import AlignmentCore
from src.support.msg_box import MessageBox
from src.support.tkconvert import TkConverter
from src.view.mapping_app import (AutoMappingViewer, EntryMappingViewer,
                                  ManualMappingViewer)


LOGGER = logging.getLogger(__name__)

class EntryMappingAction(EntryMappingViewer):
    def __init__(self):
        super().__init__()
        self._img_path = None
        self._temp_path = None

        self.btn_img_path.config(command=self._load_img_path)
        self.btn_temp_path.config(command=self._load_temp_path)
        self.btn_ok.config(command=self._confirm)

    def _load_img_path(self):
        self._img_path = askopenfilename(
            initialdir=os.path.abspath('../../'),
            title=u'選擇原始圖片路徑',
            filetypes=(('JPG Image', '*.jpg'),('JPEG Image', '*.jpeg'))
        )
        if self._img_path:
            LOGGER.info('Original Image Path - {}'.format(self._img_path))
            self.label_img_path.config(text=self._img_path)

    def _load_temp_path(self):
        self._temp_path = askdirectory(
            initialdir=os.path.abspath('../../'),
            title=u'選擇熱像儀 (灰階) 圖片資料夾'
        )
        if self._temp_path:
            LOGGER.info('ThermalCAM gray colourmap directory - {}'.format(self._temp_path))
            self.label_temp_path.config(text=self._temp_path)

    def _confirm(self):
        if self._img_path is None:
            Mbox = MessageBox()
            Mbox.alert(title='Warning', string=u'請選擇原始圖片路徑')
        elif self._temp_path is None:
            Mbox = MessageBox()
            Mbox.alert(title='Warning', string=u'請選擇熱像儀 (灰階) 圖片資料夾')
        else:
            LOGGER.info('Ready to process auto mapping.')
            self.root.destroy()
            automapping_action = AutoMappingAction(self._img_path, self._temp_path)
            automapping_action.mainloop()

class AutoMappingAction(AutoMappingViewer):
    def __init__(self, img_path, temp_path):
        super().__init__()
        self._img_path = img_path
        self._temp_path = temp_path
        self._show_img = None
        self._alignment = None
        self.run()

        self.button_ok.config(command=self.output)

    # update the output image once
    def _update_result_img(self):
        if self._show_img is not None:
            self.show_photo = TkConverter.cv2_to_photo(self._show_img)
            self.label_mapping_result.config(image=self.show_photo)
        else:
            Mbox = MessageBox()
            Mbox.alert(title='Warning', string=u'無法自動對應, 請嘗試手動定位')

    # output transform matrix
    def output(self):
        if self.alignment is not None:
            save_path = self._img_path.split(os.sep)
            save_path[-1] = save_path[-1].split('.')[0]
            save_path = os.sep.join(save_path)

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            save_file = os.sep.join((save_path, 'transform_matrix.txt'))
            self.alignment.transform_matrix.tofile(save_file)
            LOGGER.info('Save transform matrix file - {}'.format(save_file))
            Mbox = MessageBox()
            Mbox.info(string='Done.', parent=self.root)
        else:
            LOGGER.error('Please do the alignment mapping first')

    # run the alignment code and get the result img
    def run(self):
        self.alignment = AlignmentCore(self._img_path, self._temp_path)
        self._show_img = self.alignment.run()
        self._update_result_img()

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
