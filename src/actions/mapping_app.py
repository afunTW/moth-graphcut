"""
Defined mapping application action
"""
import logging
import os
import sys
import time
from inspect import currentframe, getframeinfo
from tkinter.filedialog import askdirectory, askopenfilename
sys.path.append('../..')

import numpy as np

import cv2
from matplotlib import pyplot as plt
from src import tkconfig
from src.actions.alignment import AlignmentCore
from src.image.imnp import ImageNP
from src.support.msg_box import MessageBox
from src.support.tkconvert import TkConverter
from src.view.mapping_app import (AutoMappingViewer, EntryMappingViewer,
                                  ManualMappingViewer)


__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
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
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
            title=u'選擇原始圖片路徑',
            filetypes=(('JPG Image', '*.jpg'),('JPEG Image', '*.jpeg'))
        )
        if self._img_path:
            LOGGER.info('Original Image Path - {}'.format(self._img_path))
            self.label_img_path.config(text=self._img_path)

    def _load_temp_path(self):
        self._temp_path = askdirectory(
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
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

        self.button_ok.config(command=self._confirm)
        self.button_manual.config(command=self._manual)

    # update the output image once
    def _update_result_img(self):
        if self._show_img is not None:
            self.show_photo = TkConverter.cv2_to_photo(self._show_img)
            self.label_mapping_result.config(image=self.show_photo)
        else:
            Mbox = MessageBox()
            Mbox.alert(title='Warning', string=u'無法自動對應, 請嘗試手動定位')

    # manual mapping
    def _manual(self):
        LOGGER.info('Ready to process manual mapping')
        self.root.destroy()
        manualmapping = ManualMappingAction(self._img_path, self._temp_path)
        manualmapping.mainloop()

    # output transform matrix and close windows
    def _confirm(self):
        if self.alignment is not None:
            save_path = self._img_path.split(os.sep)
            save_path[-1] = save_path[-1].split('.')[0]
            save_path = os.sep.join(save_path)

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            save_file = os.sep.join((save_path, 'transform_matrix.dat'))
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

class ManualMappingAction(ManualMappingViewer):
    def __init__(self, img_path, temp_path):
        super().__init__()
        self.transform_matrix = None
        self._img_path = img_path
        self._temp_path = temp_path
        self._panel_anchor = []
        self._display_anchor = []

        # preprocess
        self._load_image()
        self._sync_anchor_state()

        # callback
        self.button_preview.config(command=self._preview)
        self.button_ok.config(command=self._confirm)

        # keyboard event
        self.root.bind('<u>', self._undo_anchor)
        self.root.bind('<U>', self._undo_anchor)

        # mouse event
        self.label_panel_image.bind(
            tkconfig.MOUSE_RELEASE_LEFT,
            lambda x: self._on_draw_anchor(x, self._panel_img, self._panel_anchor)
        )
        self.label_display_image.bind(
            tkconfig.MOUSE_RELEASE_LEFT,
            lambda x: self._on_draw_anchor(x, self._display_img, self._display_anchor)
        )

    # load image - original and first thermal image
    def _load_image(self):
        # get the first thermal image to anchor
        thermal_file = [os.path.join(self._temp_path, i) for i in os.listdir(self._temp_path)]
        thermal_file = sorted(thermal_file)[0]

        # read panel/display image
        self._panel_img = cv2.imread(self._img_path)
        self._display_img = cv2.imread(thermal_file)
        self._img_h, self._img_w = self._display_img.shape[0], self._display_img.shape[1]
        self._panel_img = cv2.resize(self._panel_img, (self._img_w, self._img_h))

        # backup original image
        self._panel_img_bk = self._panel_img.copy()
        self._display_img_bk = self._display_img.copy()

        # update and sync
        self._update_image()
        self._sync_image()

    # convert image to photo and update to panel/display
    def _update_image(self):
        try:
            # try to convert cv2 image to photo
            self._img_h, self._img_w = self._panel_img.shape[0], self._panel_img.shape[1]
            self.photo_panel = TkConverter.cv2_to_photo(self._panel_img)
            self.photo_display = TkConverter.cv2_to_photo(self._display_img)
        except Exception as e:
            # generate default ndarray image to photo
            LOGGER.warning('Cannot update image properly')
            self.photo_panel = ImageNP.generate_checkboard((239, 320), block_size=10)
            self.photo_panel = TkConverter.ndarray_to_photo(self.photo_panel)
            self.photo_display = self.photo_panel

    # sync image to panel label
    def _sync_image(self):
        self.label_panel_image.config(image=self.photo_panel)
        self.label_display_image.config(image=self.photo_display)
        if self.root and 'normal' == self.root.state():
            self.frame_body.after(10, self._sync_image)

    # sync anchor state
    def _sync_anchor_state(self):
        panel_anchor_remain = 4 - len(self._panel_anchor)
        display_anchor_remain = 4 - len(self._display_anchor)
        self.label_panel_state.config(text=u'Original - 尚餘 {} 個標記'.format(panel_anchor_remain))
        self.label_display_state.config(text=u'Thermal - 尚餘 {} 個標記'.format(display_anchor_remain))
        if self.root and 'normal' == self.root.state():
            self.frame_nav.after(10, self._sync_anchor_state)

    # redraw the anchor to image
    def _render_anchor(self):
        self._panel_img = self._panel_img_bk.copy()
        self._display_img = self._display_img_bk.copy()
        for anchor in self._panel_anchor:
            x, y = anchor[0], anchor[1]
            cv2.circle(self._panel_img, (x, y), 3, (0, 0, 255), cv2.FILLED)
        for anchor in self._display_anchor:
            x, y = anchor[0], anchor[1]
            cv2.circle(self._display_img, (x, y), 3, (0, 0, 255), cv2.FILLED)
        self._update_image()

    # get transform matrix
    def _get_transform_matrix(self):
        if len(self._panel_anchor) != 4:
            LOGGER.error('Original image should get 4 anchor points')
            Mbox = MessageBox()
            Mbox.alert(string=u'請確認左圖已標記 4 個座標點')
        elif len(self._display_anchor) != 4:
            LOGGER.error('Thermal image should get 4 anchor points')
            Mbox = MessageBox()
            Mbox.alert(string=u'請確認右圖已標記 4 個座標點')
        else:
            # get the point.x, point.y and sorted in lt, lb, rt, rb
            panel_anchor = [(point[0], point[1]) for point in self._panel_anchor]
            display_anchor = [(point[0], point[1]) for point in self._display_anchor]
            panel_anchor = sorted(panel_anchor, key=lambda point: (point[0], point[1]))
            display_anchor = sorted(display_anchor, key=lambda point: (point[0], point[1]))
            LOGGER.info('original anchor - {}'.format(panel_anchor))
            LOGGER.info('thermal anchor - {}'.format(display_anchor))
            panel_anchor = np.array(panel_anchor)
            display_anchor = np.array(display_anchor)

            # get transform matrix and generate preview image
            M, status = cv2.findHomography(display_anchor, panel_anchor)
            self.transform_matrix = M
            return M

    # callback: preview the result
    def _preview(self):
        M = self._get_transform_matrix()
        if M is not None:
            thermal_img = cv2.cvtColor(self._display_img_bk.copy(), cv2.COLOR_BGR2GRAY)
            preview_img = cv2.warpPerspective(thermal_img, M, thermal_img.shape[:2][::-1])
            mask_img = cv2.cvtColor(self._panel_img_bk.copy(), cv2.COLOR_BGR2HSV)[:, :, 2]
            ret, mask_img = cv2.threshold(mask_img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
            if mask_img[0, :].sum() > 255*5:
                mask_img[mask_img == 255] = 100
                mask_img[mask_img == 0] = 255
                mask_img[mask_img == 100] = 0
            mask_img = mask_img.astype('bool')
            preview_img[mask_img] = 0

            plt.imshow(preview_img, cmap='gray')
            plt.show()

    # callback: confirm the mapping result and output the transform matrix
    def _confirm(self):
        M = self._get_transform_matrix()
        if M is not None:
            save_path = self._img_path.split(os.sep)
            save_path[-1] = save_path[-1].split('.')[0]
            save_path = os.sep.join(save_path)

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            save_file = os.sep.join((save_path, 'transform_matrix.dat'))
            M.tofile(save_file)
            LOGGER.info('Save transform matrix file - {}'.format(save_file))
            Mbox = MessageBox()
            Mbox.info(string='Done.', parent=self.root)

    # key event: undo anchor
    def _undo_anchor(self, k):
        panel_sort_timestamp = sorted(self._panel_anchor, key=lambda x: x[-1])
        display_sort_timestamp = sorted(self._display_anchor, key=lambda x: x[-1])

        if panel_sort_timestamp and display_sort_timestamp:
            panel_last = panel_sort_timestamp[-1]
            display_last = display_sort_timestamp[-1]
            if panel_last[-1] > display_last[-1]:
                self._panel_anchor.pop()
            elif display_last[-1] > panel_last[-1]:
                self._display_anchor.pop()
        elif panel_sort_timestamp and not display_sort_timestamp:
            self._panel_anchor.pop()
        elif not panel_sort_timestamp and display_sort_timestamp:
            self._display_anchor.pop()
        else:
            LOGGER.warning('No recorded anchor to undo')

        self._render_anchor()

    # mouse event: draw anchor on panel/display
    def _on_draw_anchor(self, event=None, img=None, record=None):
        if img is None:
            LOGGER.error('No given image')
        if record is None or not isinstance(record, list):
            LOGGER.error('No given record')
        elif len(record) >= 4:
            LOGGER.warning('already got {} anchors'.format(len(record)))
        else:
            LOGGER.info('Mouse x={}, y={}'.format(event.x, event.y))
            cv2.circle(img, (event.x, event.y), 3, (0, 0, 255), cv2.FILLED)
            record.append((event.x, event.y, time.time()))
            self._update_image()


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
