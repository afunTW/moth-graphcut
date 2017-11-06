import logging
import os
import sys
import tkinter
from inspect import currentframe, getframeinfo
from tkinter import ttk
from tkinter.filedialog import askopenfilenames
sys.path.append('../..')

import cv2
from src import tkconfig
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.graphcut_app import GraphCutViewer

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)
STATE = ['browse', 'edit']

class GraphCutAction(GraphCutViewer):
    def __init__(self):
        super().__init__()
        self.instruction = None
        self._image_queue = []
        self._current_image_info = {}
        self._current_state = None

        # callback
        self.scale_gamma.config(command=self._update_scale_gamma_msg)
        self.scale_manual_threshold.config(command=self._update_scale_manual_threshold_msg)
        for radiobtn in self.radiobtn_threshold_options:
            radiobtn.config(command=self._update_scale_manual_threshold_state)

        # keyboard
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

    # check and update image to given widget
    def _check_and_update_photo(self, target_widget, photo=None):
        try:
            assert photo is not None
            target_widget.config(image=photo)
        except Exception as e:
            self._default_photo = ImageNP.generate_checkboard(
                (self._im_h, self._im_w), 10)
            self._default_photo = TkConverter.ndarray_to_photo(
                self._default_photo)
            target_widget.config(image=self._default_photo)

    # check and update image to input panel
    def _check_and_update_panel(self, img=None):
        try:
            assert img is not None
            self.photo_panel = TkConverter.cv2_to_photo(img)
            self._check_and_update_photo(
                self.label_panel_image, self.photo_panel)
        except Exception as e:
            self._check_and_update_photo(self.label_panel_image, None)

    # check and update image to display
    def _check_and_update_display(self, img=None):
        try:
            assert img is not None
            self.photo_display = TkConverter.cv2_to_photo(img)
            self._check_and_update_photo(
                self.label_display_image, self.photo_display)
        except Exception as e:
            self._check_and_update_photo(self.label_display_image, None)

    # move line to left or right and check boundary
    def _check_and_move_line(self, line, step=0):
        try:
            assert len(line) == 2
            ptx1, ptx2 = line
            assert len(ptx1) == 2 and len(ptx2) == 2
            pty1, pty2 = (ptx1[0]+step, ptx1[1]), (ptx2[0]+step, ptx2[1])
            pty1 = (min(max(0, pty1[0]), self._im_w), pty1[1])
            pty2 = (min(max(0, pty2[0]), self._im_w), pty2[1])
            return (pty1, pty2)
        except Exception as e:
            LOGGER.exception(e)

    # move line to left and update to panel
    def _check_and_update_symmetry(self, step=0):
        if 'symmetry' in self._current_image_info:
            newline = self._check_and_move_line(self._current_image_info['symmetry'], step)
            if not newline:
                LOGGER.error('Failed to move symmetry line')
            else:
                self._current_image_info['symmetry'] = newline
                self._render_panel_image()

    # switch to different state
    def _switch_state(self, state):
        '''
        brose mode - switch to previous/next image
        edit mode - computer vision operation
        '''
        if not self._image_queue:
            LOGGER.warn('No images in the image queue')
            self.input_images()

        elif state is None or not state or state not in STATE:
            LOGGER.error('{} not in standard state'.format(state))

        elif state == 'browse':

            # update state message
            self._current_state = 'browse'
            self.label_state.config(text=u'瀏覽模式 ({}/{}) - {}'.format(
                self._current_image_info['index'] + 1,
                len(self._image_queue),
                self._current_image_info['path'].split(os.sep)[-1]
            ), style='H2BlackdBold.TLabel')

            # update display default photo
            self._check_and_update_display(None)

            # rebind the keyboard event
            self.root.bind(tkconfig.KEY_UP, self._k_switch_to_previous_image)
            self.root.bind(tkconfig.KEY_LEFT, self._k_switch_to_previous_image)
            self.root.bind(tkconfig.KEY_DOWN, self._k_switch_to_next_image)
            self.root.bind(tkconfig.KEY_RIGHT, self._k_switch_to_next_image)

        elif state == 'edit':

            # update state message
            self._current_state = 'edit'
            self.label_state.config(text=u'編輯模式 ({}/{}) - {}'.format(
                self._current_image_info['index'] + 1,
                len(self._image_queue),
                self._current_image_info['path'].split(os.sep)[-1]
            ), style='H2RedBold.TLabel')

            # generate symmetry line
            self._current_image_info['panel'] = self._current_image_info['image'].copy()
            self._current_image_info['symmetry'] = ImageNP.generate_symmetric_line(self._current_image_info['panel'])
            self._render_panel_image()

            # rebind the keyboard event
            self.root.bind(tkconfig.KEY_LEFT, lambda x: self._check_and_update_symmetry(step=-1))
            self.root.bind(tkconfig.KEY_RIGHT, lambda x: self._check_and_update_symmetry(step=1))
            self.root.bind(tkconfig.KEY_PAGEDOWN, lambda x: self._check_and_update_symmetry(step=-10))
            self.root.bind(tkconfig.KEY_PAGEUP, lambda x: self._check_and_update_symmetry(step=10))

    # render panel image
    def _render_panel_image(self):
        if not self._image_queue:
            LOGGER.error('No image in the queue to process')
        elif self._current_state != 'edit':
            LOGGER.error('You cannot render panel image in {} state'.format(self._current_state))
        elif not self._current_image_info or 'panel' not in self._current_image_info:
            LOGGER.error('No processing image to render')
        else:
            self._current_image_info['panel'] = self._current_image_info['image'].copy()
            if 'symmetry' in self._current_image_info:
                pt1, pt2 = self._current_image_info['symmetry']
                cv2.line(self._current_image_info['panel'], pt1, pt2, [0, 0, 0], 2)

            self._check_and_update_panel(img=self._current_image_info['panel'])

    # reset algorithm parameter
    def _reset_parameter(self):
        self.val_scale_gamma.set(1.0)
        self.val_threshold_option.set('manual')
        self.val_manual_threshold.set(250)

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

    # callback: drag the ttk.Scale and show the current value
    def _update_scale_gamma_msg(self, val_gamma):
        val_gamma = float(val_gamma)
        self.label_gamma.config(text=u'調整對比 ({:.2f}): '.format(val_gamma))

    # callback: drag the ttk.Scale and show the current value
    def _update_scale_manual_threshold_msg(self, val_threshold):
        val_threshold = float(val_threshold)
        self.label_manual_threshold.config(text=u'門檻值 ({:.2f}): '.format(val_threshold))

    # callback: disable the manual scale when the option is not the manual threshold
    def _update_scale_manual_threshold_state(self):
        val_option = self.val_threshold_option.get()
        if val_option == 'manual':
            self.scale_manual_threshold.state(('active', '!disabled'))
        else:
            self.scale_manual_threshold.state(('disabled', '!active'))

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
                self._check_and_update_panel(self._current_image_info['image'])
                self._check_and_update_display(None)
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
                    current_index, current_index + step
                ))
            else:
                target_index = min(current_index + step,
                                   len(self._image_queue) - 1)
                self._update_current_image(index=target_index)
                self._check_and_update_panel(self._current_image_info['image'])
                self._check_and_update_display(None)
        else:
            LOGGER.warning('No given image')

    # open filedialog to get input image paths
    def input_images(self):
        initdir = os.path.abspath(os.path.join(__FILE__, '../../../'))
        paths = askopenfilenames(
            title=u'請選擇要去背的圖片',
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
            self._check_and_update_panel(self._current_image_info['image'])
            self._check_and_update_display(None)

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

    graphcut_action = GraphCutAction()
    graphcut_action.input_images()
    graphcut_action.mainloop()
