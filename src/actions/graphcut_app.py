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
from src.support.msg_box import Instruction, MessageBox
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
        self._init_instruction()

        # color
        self._color_body_line = [255, 0, 0]
        self._color_track_line = [0, 0, 0]

        # flag
        self._flag_body_width = False
        self._flag_drawing_left = False
        self._flag_drew_left = False
        self._flag_drawing_right = False
        self._flag_drew_right = False

        # callback
        self.scale_gamma.config(command=self._update_scale_gamma_msg)
        self.scale_manual_threshold.config(command=self._update_scale_manual_threshold_msg)
        for radiobtn in self.radiobtn_threshold_options:
            radiobtn.config(command=self._update_scale_manual_threshold_state)

        # keyboard
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

    @property
    def flag_was_modified(self):
        flag_option = [self._flag_body_width]
        return any(flag_option)

    # init instruction
    def _init_instruction(self):
        self.instruction = Instruction(title=u'提示視窗')
        self.instruction.row_append(u'ESC', u'進入瀏覽模式')
        self.instruction.row_append(u'ENTER', u'進入編輯模式')
        self.instruction.row_append(u'UP/LEFT (瀏覽模式)', u'切換至上一張圖片')
        self.instruction.row_append(u'DOWN/RIGHT (瀏覽模式)', u'切換至下一張圖片')
        self.instruction.row_append(u'LEFT/RIGHT (編輯模式)', u'移動鏡像中線 1 pixel')
        self.instruction.row_append(u'PAGE_DOWN/PAGE_UP (編輯模式)', u'移動鏡像中線 10 pixel')
        self.instruction.row_append(u'h/H', u'打開提示視窗')

    # check and update image to given widget
    def _check_and_update_photo(self, target_widget, photo=None):
        try:
            assert photo is not None
            target_widget.config(image=photo)
        except Exception as e:
            self._default_photo = ImageNP.generate_checkboard((self._im_h, self._im_w), 10)
            self._default_photo = TkConverter.ndarray_to_photo(self._default_photo)
            target_widget.config(image=self._default_photo)

    # check and update image to input panel
    def _check_and_update_panel(self, img=None):
        try:
            assert img is not None
            self.photo_panel = TkConverter.cv2_to_photo(img)
            self._check_and_update_photo(self.label_panel_image, self.photo_panel)
        except Exception as e:
            self._check_and_update_photo(self.label_panel_image, None)

    # check and update image to display panel
    def _check_and_update_display(self):
        self.photo_small = ImageNP.generate_checkboard((self._im_h//2, self._im_w//3), 10)
        self.photo_small = TkConverter.ndarray_to_photo(self.photo_small)
        self.photo_large = ImageNP.generate_checkboard((self._im_h, self._im_w//3), 10)
        self.photo_large = TkConverter.ndarray_to_photo(self.photo_large)
        self._check_and_update_fl(None)
        self._check_and_update_fr(None)
        self._check_and_update_bl(None)
        self._check_and_update_br(None)
        self._check_and_update_body(None)

    # check and update image to fl
    def _check_and_update_fl(self, img=None):
        try:
            assert img is not None
            self.photo_fl = TkConverter.cv2_to_photo(img)
            self._check_and_update_photo(self.label_fl_image, self.photo_fl)
        except Exception as e:
            self._check_and_update_photo(self.label_fl_image, self.photo_small)

    # check and update image to fr
    def _check_and_update_fr(self, img=None):
        try:
            assert img is not None
            self.photo_fr = TkConverter.cv2_to_photo(img)
            self._check_and_update_photo(self.label_fr_image, self.photo_fr)
        except Exception as e:
            self._check_and_update_photo(self.label_fr_image, self.photo_small)

    # check and update image to bl
    def _check_and_update_bl(self, img=None):
        try:
            assert img is not None
            self.photo_bl = TkConverter.cv2_to_photo(img)
            self._check_and_update_photo(self.label_bl_image, self.photo_bl)
        except Exception as e:
            self._check_and_update_photo(self.label_bl_image, self.photo_small)

    # check and update image to br
    def _check_and_update_br(self, img=None):
        try:
            assert img is not None
            self.photo_br = TkConverter.cv2_to_photo(img)
            self._check_and_update_photo(self.label_br_image, self.photo_br)
        except Exception as e:
            self._check_and_update_photo(self.label_br_image, self.photo_small)

    # check and update image to fr
    def _check_and_update_body(self, img=None):
        try:
            assert img is not None
            self.photo_body = TkConverter.cv2_to_photo(img)
            self._check_and_update_photo(self.label_body_image, self.photo_body)
        except Exception as e:
            self._check_and_update_photo(self.label_body_image, self.photo_large)

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

    # draw lines by point record
    def _draw_lines_by_points(self, img, track, color=(255, 255, 255)):
        for i, record in enumerate(track):
            if len(record) > 2:
                img = self._draw_lines_by_points(img, record, color=color)
            elif i == 0:
                continue
            else:
                cv2.line(img, track[i-1], record, color, 2)
        return img

    # core function to separate component
    def _separate_component(self):
        if self._current_state != 'edit':
            LOGGER.warning('Not avaliable to separate component in {} state'.format(self._current_state))
        elif 'image' not in self._current_image_info:
            LOGGER.warning('No process image')
        elif not self._flag_body_width:
            LOGGER.warning('Please confirm the body length first')
        elif 'l_track' not in self._current_image_info or 'r_track' not in self._current_image_info:
            LOGGER.warning('No tracking label')
        else:
            display_image = self._current_image_info['image'].copy()
            display_image = self._separate_component_by_track_and_line(display_image)
            display_fl = self._separate_component_by_coor(display_image.copy(), 'fl', crop=True)
            display_fr = self._separate_component_by_coor(display_image.copy(), 'fr', crop=True)
            display_bl = self._separate_component_by_coor(display_image.copy(), 'bl', crop=True)
            display_br = self._separate_component_by_coor(display_image.copy(), 'br', crop=True)
            # test
            self._check_and_update_fl(display_fl)
            self._check_and_update_fr(display_fr)
            self._check_and_update_bl(display_bl)
            self._check_and_update_br(display_br)

    # eliminate image by track and line
    def _separate_component_by_track_and_line(self, img):
        if 'image' not in self._current_image_info:
            LOGGER.warning('No process image')
        else:
            if 'l_line' in self._current_image_info:
                img = self._draw_lines_by_points(img, self._current_image_info['l_line'])
            if 'r_line' in self._current_image_info:
                img = self._draw_lines_by_points(img, self._current_image_info['r_line'])
            if 'l_track' in self._current_image_info:
                img = self._draw_lines_by_points(img, self._current_image_info['l_track'])
            if 'r_track' in self._current_image_info:
                img = self._draw_lines_by_points(img, self._current_image_info['r_track'])
            return img

    # removal image background by given x and y and part
    def _separate_component_by_coor(self, img, part, crop=False):
        bottom_y = lambda track: max([ptx[1] for ptx in track])
        top_y = lambda track: min([ptx[1] for ptx in track])
        l_ptx = self._current_image_info['l_line'][0][0]
        r_ptx = self._current_image_info['r_line'][0][0]

        if part == 'fl':
            x = l_ptx
            y = bottom_y(self._current_image_info['l_track'])
            img[:, x:] = 255
            img[y:, :] = 255
            if crop:
                img = img[:y, :x]
        elif part == 'fr':
            x = r_ptx
            y = bottom_y(self._current_image_info['r_track'])
            img[:, :x] = 255
            img[y:, :] = 255
            if crop:
                img = img[:y, x:]
        elif part == 'bl':
            x = l_ptx
            y = top_y(self._current_image_info['l_track'])
            img[:, x:] = 255
            img[:y, :] = 255
            if crop:
                img = img[y:, :x]
        elif part == 'br':
            x = r_ptx
            y = top_y(self._current_image_info['r_track'])
            img[:, :x] = 255
            img[:y, :] = 255
            if crop:
                img = img[y:, x:]
        return img

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
            self._check_and_update_display()

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

            # bind the mouse event
            self.label_panel_image.bind(tkconfig.MOUSE_MOTION, self._m_check_and_update_body_width)
            self.label_panel_image.bind(tkconfig.MOUSE_RELEASE_LEFT, self._m_confirm_body_width)

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
            if 'l_line' in self._current_image_info:
                pt1, pt2 = self._current_image_info['l_line']
                cv2.line(self._current_image_info['panel'], pt1, pt2, self._color_body_line, 2)
            if 'r_line' in self._current_image_info:
                pt1, pt2 = self._current_image_info['r_line']
                cv2.line(self._current_image_info['panel'], pt1, pt2, self._color_body_line, 2)
            if 'l_track' in self._current_image_info:
                for i, ptx in enumerate(self._current_image_info['l_track']):
                    if i == 0: continue
                    pt1, pt2 = self._current_image_info['l_track'][i-1], ptx
                    cv2.line(self._current_image_info['panel'], pt1, pt2, self._color_track_line, 2)
            if 'r_track' in self._current_image_info:
                for i, ptx in enumerate(self._current_image_info['r_track']):
                    if i == 0: continue
                    pt1, pt2 = self._current_image_info['r_track'][i-1], ptx
                    cv2.line(self._current_image_info['panel'], pt1, pt2, self._color_track_line, 2)

            self._check_and_update_panel(img=self._current_image_info['panel'])

    # reset algorithm parameter
    def _reset_parameter(self):
        # reset
        self._color_body_line = [255, 0, 0]
        self.val_scale_gamma.set(1.0)
        self.val_threshold_option.set('manual')
        self.val_manual_threshold.set(250)

        # update to message widget
        self._update_scale_gamma_msg(self.val_scale_gamma.get())
        self._update_scale_manual_threshold_msg(self.val_manual_threshold.get())

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

    # mouse: check and update body line
    def _m_check_and_update_body_width(self, event=None):
        if self._current_state == 'edit':
            if 'symmetry' not in self._current_image_info:
                LOGGER.warning('No symmetry line')
            else:
                middle_line = self._current_image_info['symmetry']
                middle_x = middle_line[0][0]
                body_width = abs(event.x - middle_x)
                l_ptx = max(0, middle_x-body_width)
                r_ptx = min(middle_x+body_width, self._im_w)
                self._current_image_info['l_line'] = ((l_ptx, 0), (l_ptx, self._im_h))
                self._current_image_info['r_line'] = ((r_ptx, 0), (r_ptx, self._im_h))
                self._render_panel_image()

    # mouse: confirm body line and unbind mouse motion
    def _m_confirm_body_width(self, event=None):
        # confirm body width
        self._color_body_line = [0, 0, 255]
        self.label_panel_image.unbind(tkconfig.MOUSE_MOTION)
        body_width = abs(event.x-self._current_image_info['symmetry'][0][0])
        self._render_panel_image()

        # record and set flag
        self._current_image_info['body_width'] = body_width
        self._flag_body_width = True

        # bind the next phase mouse event
        self.label_panel_image.bind(tkconfig.MOUSE_BUTTON_LEFT, self._m_lock_track_flag)
        self.label_panel_image.bind(tkconfig.MOUSE_MOTION_LEFT, self._m_track_separate_label)
        self.label_panel_image.bind(tkconfig.MOUSE_RELEASE_LEFT, self._m_unlock_track_flag)

        # unbind symmetry line movement
        self.root.unbind(tkconfig.KEY_LEFT)
        self.root.unbind(tkconfig.KEY_RIGHT)

    # mouse: get the track label to separate moth component
    def _m_track_separate_label(self, event=None):
        '''
        Condition of tracking separate label
        e.g. on the left side
        - not was_left and not was_right: mirror
        - not was_left and was_right: reset left and record left
        - was_left and not was_right: reset all and mirror
        - was_left and was_right: reset left and record left
        '''
        if 'panel' not in self._current_image_info:
            LOGGER.error('No image to process')
        elif not self._flag_body_width:
            LOGGER.error('Please to confirm the body width first')
        elif not self._flag_drawing_left and not self._flag_drawing_right:
            LOGGER.debug('Not in the drawing mode')
        else:
            point_x = lambda x: x[0][0]
            mirror_distance = lambda x: abs(x-point_x(self._current_image_info['symmetry']))

            # on the left side
            if self._flag_drawing_left:
                if 0 <= event.x <= point_x(self._current_image_info['l_line']):
                    self._current_image_info['l_track'].append((event.x, event.y))
                    if not self._flag_drew_right:
                        self._current_image_info['r_track'].append((event.x+mirror_distance(event.x)*2, event.y))
                else:
                    self._m_unlock_track_flag()

            # on the right side
            if self._flag_drawing_right:
                if point_x(self._current_image_info['r_line']) <= event.x <= self._im_w:
                    self._current_image_info['r_track'].append((event.x, event.y))
                    if not self._flag_drew_left:
                        self._current_image_info['l_track'].append((event.x-mirror_distance(event.x)*2, event.y))
                else:
                    self._m_unlock_track_flag()

            if self._flag_drawing_left or self._flag_drawing_right:
                self._render_panel_image()

    # mouse: lock to draw left or right
    def _m_lock_track_flag(self, event=None):
        # check
        if 'l_track' not in self._current_image_info:
            self._current_image_info['l_track'] = []
        if 'r_track' not in self._current_image_info:
            self._current_image_info['r_track'] = []

        # lock and logic operation
        if 'symmetry' not in self._current_image_info:
            LOGGER.error('Please confirm body width first')

        elif 0 <= event.x <= self._current_image_info['l_line'][0][0]:
            self._flag_drawing_left = True
            self._flag_drew_left = False
            self._current_image_info['l_track'] = []
            if not self._flag_drew_right:
                self._current_image_info['r_track'] = []
            LOGGER.info('Lock the LEFT flag')

        elif self._current_image_info['r_line'][0][0] <= event.x <= self._im_w:
            self._flag_drawing_right = True
            self._flag_drew_right = False
            self._current_image_info['r_track'] = []
            if not self._flag_drew_left:
                self._current_image_info['l_track'] = []
            LOGGER.info('Lock the RIGHT flag')

    # mouse: unlock to confirm draw left or right
    def _m_unlock_track_flag(self, event=None):
        if 'symmetry' not in self._current_image_info:
            LOGGER.error('Please confirm body width first')
        elif self._flag_drawing_left:
            self._flag_drawing_left = False
            self._flag_drew_left = True
            self._separate_component()
            LOGGER.info('Unlock the LEFT flag')
        elif self._flag_drawing_right:
            self._flag_drawing_right = False
            self._flag_drew_right = True
            self._separate_component()
            LOGGER.info('Unlock the RIGHT flag')

        if self._flag_drawing_left:
            self._flag_drawing_left = False
            LOGGER.warning('Unlock the LEFT flag improperly')
        if self._flag_drawing_right:
            self._flag_drawing_right = False
            LOGGER.warning('Unlock the RIGHT flag improperly')

    # keyboard: show instruction
    def _k_show_instruction(self, event=None):
        if self.instruction is None:
            LOGGER.error('Please init instruction window first')
        else:
            self.instruction.show()

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
                self._check_and_update_display()
                self._reset_parameter()
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
                self._check_and_update_display()
                self._reset_parameter()
        else:
            LOGGER.warning('No given image')

    # auto fit the image hight from original image to resize image
    def auto_resize(self, image, ratio=0.5):
        screen_h = self.root.winfo_screenheight()
        screen_w = self.root.winfo_screenwidth()
        image_h, image_w, image_channel = image.shape
        resize_h = screen_h * ratio
        resize_w = (resize_h / image_h) * image_w
        resize_h, resize_w = int(resize_h), int(resize_w)
        image = cv2.resize(image, (resize_w, resize_h),
                           interpolation=cv2.INTER_AREA)
        LOGGER.info('resize image from {}x{} to {}x{}'.format(
            image_w, image_h, int(resize_w), int(resize_h)
        ))
        return image

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
            self._check_and_update_display()

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
