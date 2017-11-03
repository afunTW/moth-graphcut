import logging
import os
import sys
from inspect import currentframe, getframeinfo
from tkinter.filedialog import askopenfilenames
sys.path.append('../..')

import cv2
from src import tkconfig
from src.image.imnp import ImageNP
from src.support.msg_box import Instruction
from src.support.tkconvert import TkConverter
from src.view.removal_app import RemovalViewer

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)
STATE = ['browse', 'edit']

class RemovalAction(RemovalViewer):
    def __init__(self):
        super().__init__()
        self.instruction = None
        self._image_queue = []
        self._current_image_info = {}
        self._current_state = None

        # init
        self._init_instruction()

        # callback
        self.scale_threshold.config(command=self._update_floodfill_threshold)
        self.scale_iter.config(command=self._update_floodfill_iteration)

        # keyboard binding
        self.root.bind('h', self._k_show_instruction)
        self.root.bind('H', self._k_show_instruction)
        self.root.bind(tkconfig.KEY_UP, self._k_switch_to_previous_image)
        self.root.bind(tkconfig.KEY_LEFT, self._k_switch_to_previous_image)
        self.root.bind(tkconfig.KEY_DOWN, self._k_switch_to_next_image)
        self.root.bind(tkconfig.KEY_RIGHT, self._k_switch_to_next_image)
        self.root.bind(tkconfig.KEY_ESC, lambda x: self._switch_state('browse'))
        self.root.bind(tkconfig.KEY_ENTER, lambda x: self._switch_state('edit'))

    @property
    def current_image(self):
        if self._current_image_info and 'path' in self._current_image_info:
            return self._current_image_info['path']
        else:
            return False

    # init instruction
    def _init_instruction(self):
        self.instruction = Instruction(title=u'提示視窗')
        self.instruction.row_append('ESC', u'進入瀏覽模式')
        self.instruction.row_append('ENTER', u'進入編輯模式')
        self.instruction.row_append('UP/LEFT', u'在瀏覽模式下切換至上一張圖片')
        self.instruction.row_append('DOWN/RIGHT', u'在瀏覽模式下切換至下一張圖片')
        self.instruction.row_append('h/H', u'打開提示視窗')

    # check and update image to given widget
    def _check_and_update_photo(self, target_widget, img=None):
        try:
            assert img is not None
            self._tmp_photo = TkConverter.cv2_to_photo(img)
            target_widget.config(image=self._tmp_photo)
        except Exception as e:
            self._default_photo = ImageNP.generate_checkboard((self._im_h, self._im_w), 10)
            self._default_photo = TkConverter.ndarray_to_photo(self._default_photo)
            target_widget.config(image=self._default_photo)

    # switch to state and update related action
    def _switch_state(self, state):
        '''
        brose mode - switch to previous/next image
        edit mode - computer vision operation
        '''
        if state is None or not state or state not in STATE:
            LOGGER.error('{} not in standard state'.fornat(state))
        elif state == 'browse':
            self._current_state = 'browse'
            self.label_state.config(text=u'瀏覽模式 ({}/{}) - {}'.format(
                self._current_image_info['index']+1,
                len(self._image_queue),
                self._current_image_info['path'].split(os.sep)[-1]
            ), style='H2BlackdBold.TLabel')
        elif state == 'edit':
            self._current_state = 'edit'
            self.label_state.config(text=u'編輯模式 ({}/{}) - {}'.format(
                self._current_image_info['index'] + 1,
                len(self._image_queue),
                self._current_image_info['path'].split(os.sep)[-1]
            ), style='H2RedBold.TLabel')

    # update current image
    def _update_current_image(self, index):
        '''
        - record current image index, path
        - read image
        - resize image
        - record current image resize info
        - update size message
        - reset algorithm parameters
        - reset state to browse
        '''
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
            self._im_h, self._im_w = self._current_image_info['resize']
            self._reset_parameter()
            self._switch_state(state='browse')

    # update floodfill threshold
    def _update_floodfill_threshold(self, val_threshold):
        val_threshold = float(val_threshold)
        self.label_floodfill_threshold.config(text=u'門檻值 ({:.2f}): '.format(val_threshold))

    # update floodfill iteration count
    def _update_floodfill_iteration(self, val_iter):
        val_iter = float(val_iter)
        self.label_floodfill_iter.config(text=u'迭代次數 ({:2.0f}): '.format(val_iter))

    # reset algorithm parameter
    def _reset_parameter(self):
        self.val_scale_threshold.set(0.85)
        self._update_floodfill_threshold(0.85)
        self.val_scale_iter.set(5)
        self._update_floodfill_iteration(5)

    # keyboard: switch to previous image
    def _k_switch_to_previous_image(self, event=None, step=1):
        if self._current_state is None or self._current_state != 'browse':
            LOGGER.warning('Not in browse mode, cannot switch image')
        elif self.current_image and self.current_image in self._image_queue:
            current_index = self._image_queue.index(self.current_image)
            if current_index == 0:
                LOGGER.warning('Already the first image in the queue')
            elif current_index - step < 0:
                LOGGER.warning('Out of index: current {}, target {}'.format(
                    current_index, current_index - step
                ))
            else:
                target_index = max(0, current_index - step)
                self._update_current_image(index=target_index)
                self._check_and_update_photo(self.label_panel_image, self._current_image_info['image'])
                self._check_and_update_photo(self.label_display_image, None)
        else:
            LOGGER.warning('No given image')

    # keyboard: switch to next image
    def _k_switch_to_next_image(self, event=None, step=1):
        if self._current_state is None or self._current_state != 'browse':
            LOGGER.warning('Not in browse mode, cannot switch image')
        elif self.current_image and self.current_image in self._image_queue:
            current_index = self._image_queue.index(self.current_image)
            if current_index == len(self._image_queue) - 1:
                LOGGER.warning('Already the last image in the queue')
            elif current_index + step >= len(self._image_queue):
                LOGGER.warning('Out of index: current {}, target {}'.format(
                    current_index, current_index+step
                ))
            else:
                target_index = min(current_index+step, len(self._image_queue)-1)
                self._update_current_image(index=target_index)
                self._check_and_update_photo(self.label_panel_image, self._current_image_info['image'])
                self._check_and_update_photo(self.label_display_image, None)
        else:
            LOGGER.warning('No given image')

    # keyboard: show instruction
    def _k_show_instruction(self, event=None):
        if self.instruction is None:
            LOGGER.error('Please init instruction window first')
        else:
            self.instruction.show()

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

            # update first image to input panel and change display default bg
            self._update_current_image(index=0)
            self._check_and_update_photo(self.label_panel_image, self._current_image_info['image'])
            self._check_and_update_photo(self.label_display_image, None)

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
