import logging
import os
import sys
from inspect import currentframe, getframeinfo
from tkinter.filedialog import askopenfilenames
sys.path.append('../..')

import cv2
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.removal_app import RemovalViewer

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)

class RemovalAction(RemovalViewer):
    def __init__(self):
        super().__init__()
        self._current_image_info = {}
        self._image_queue = []

    @property
    def current_image(self):
        if self._current_image_info and 'path' in self._current_image_info:
            return self._current_image_info['path']
        else:
            return False

    def _check_and_update_photo(self, target_widget, img):
        try:
            self._tmp_photo = TkConverter.cv2_to_photo(img)
            target_widget.config(image=self._tmp_photo)
        except Exception as e:
            self._default_photo = ImageNP.generate_checkboard((self._im_h, self._im_w), 10)
            self._default_photo = TkConverter.ndarray_to_photo(self._default_photo)
            target_widget.config(image=self._tmp_photo)

    # update current image
    def _update_current_image(self, index):
        if self._image_queue is None or not self._image_queue:
            LOGGER.warning('No images in the queue')
        elif index < 0 or index >= len(self._image_queue):
            LOGGER.error('Image queue out of index')
        else:
            self._current_image_info = {
                'index': index,
                'path': self._image_queue[index],
                'image': cv2.imread(self._image_queue[index])
            }
            LOGGER.info('Read image - {}'.format(self._current_image_info['path']))
            self._current_image_info['size'] = self._current_image_info['image'].shape[:2]
            self._current_image_info['image'] = self.auto_resize(self._current_image_info['image'])
            self._current_image_info['resize'] = self._current_image_info['image'].shape[:2]
            self.label_resize.config(text=u'原有尺寸 {}X{} -> 顯示尺寸 {}X{}'.format(
                *self._current_image_info['size'][::-1], *self._current_image_info['resize'][::-1]
            ))

    # open filedialog to get input image paths
    def input_images(self):
        initdir = os.path.abspath(os.path.join(__FILE__, '../../../'))
        paths = askopenfilenames(
            title=u'請選擇要去被的圖片',
            filetypes=[('JPG file (*.jpg)', '*jpg'),
                       ('JPEG file (*.jpeg)', '*.jpeg'),
                       ('PNG file (*.png)', '*.png')],
            initialdir=initdir,
            parent=self.root
        )

        if paths:
            self._image_queue = list(paths)

            # update first image to input panel
            self._update_current_image(index=0)
            self._check_and_update_photo(self.label_panel_image, self._current_image_info['image'])

    # auto fit the image hight from original image to resize image
    def auto_resize(self, image, ratio=0.5):
        screen_h = self.root.winfo_screenheight()
        screen_w = self.root.winfo_screenwidth()
        image_h, image_w, image_channel = image.shape
        resize_h = screen_h * ratio
        resize_w = (resize_h / image_h) * image_w
        resize_h, resize_w = int(resize_h), int(resize_w)
        image = cv2.resize(image, (resize_w, resize_h),interpolation=cv2.INTER_AREA)
        LOGGER.info('resize image from {}x{} to {}x{}'.format(
            image_w, image_h, int(resize_w), int(resize_h)
        ))
        return image


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    removal_action = RemovalAction()
    removal_action.input_images()
    removal_action.mainloop()
