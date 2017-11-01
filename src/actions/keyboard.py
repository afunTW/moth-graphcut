"""
Defined callback functions of keyboard event
"""
import logging
import sys

import cv2

sys.path.append('../')
from src.image.imnp import ImageNP
from src.image.imcv import ImageCV
from src.support.profiling import func_profiling
from src.view.template import (GraphcutViewer, ImageViewer,
                               PreprocessViewer)

LOGGER = logging.getLogger(__name__)

class KeyboardHandler(ImageViewer):
    def __init__(self):
        super().__init__()

    # doing nothing
    def stale(self, event=None):
        pass

    # press UP and switch to previous image in image queue
    @func_profiling
    def switch_to_previous_image(self, event=None, step=1):
        if self.current_image_path and self.current_image_path in self.image_queue:
            current_index = self.image_queue.index(self.current_image_path)
            if current_index == 0:
                LOGGER.warning('Already operated the first image in the queue')
            elif current_index - step < 0:
                LOGGER.warning('Out of index: current {}, target {}'.format(
                    current_index, current_index-step
                ))
            else:
                target_index = max(0, current_index-step)
                self.current_image_path = self.image_queue[target_index]
                self._init_state()
                self._update_image(self.current_image_path)
        else:
            LOGGER.warning('No given image')

    # press DOWN and switch to next image in image queue
    @func_profiling
    def switch_to_next_image(self, event=None, step=1):
        if self.current_image_path and self.current_image_path in self.image_queue:
            current_index = self.image_queue.index(self.current_image_path)
            if current_index == len(self.image_queue) - 1:
                LOGGER.warning('Already operated the last image in the queue')
            elif current_index + step >= len(self.image_queue):
                LOGGER.warning('Out of index: current {}, target {}'.format(
                    current_index, current_index+step
                ))
            else:
                target_index = min(current_index+step, len(self.image_queue)-1)
                self.current_image_path = self.image_queue[target_index]
                self._init_state()
                self._update_image(self.current_image_path)
        else:
            LOGGER.warning('No given image')

class PreprocessKeyboard(KeyboardHandler, PreprocessViewer):
    def __init__(self):
        super().__init__()

    # press ESC to leave edit mode
    def enter_view_mode(self, event=None):
        self.state_message = 'view'
        self.root_state = ['view']

    # press ENTER and switch appication state into EDIT
    @func_profiling
    def enter_edit_mode(self, event=None, threshold=0.9, iter_blur=5):
        self.state_message = 'edit'
        self.root_state.append('edit')

        # show the default display image
        display_image = ImageCV.run_floodfill(self.image_panel, threshold, iter_blur)
        self._update_display(display_image)
        self.root_state.append('result')

    # press UP and switch to previous image in image queue
    def switch_to_previous_image(self, event=None, step=1):
        if 'edit' in self.root_state:
            LOGGER.warning('Can not go the previous image in edit mode')
        elif 'view' in self.root_state:
            super().switch_to_previous_image(event=event, step=step)
        else:
            LOGGER.error('Unexpected state {}'.format(self.root_state))

    # press DOWN and switch to next image in image queue
    def switch_to_next_image(self, event=None, step=1):
        if 'edit' in self.root_state:
            LOGGER.warning('Can not go the next image in edit mode')
        elif 'view' in self.root_state:
            super().switch_to_next_image(event=event, step=step)
        else:
            LOGGER.error('Unexpected state {}'.format(self.root_state))

    # press SPACE to save the image
    def save_display_image(self, event=None):
        if self._image_original is None:
            LOGGER.warning('No original image to process')
        elif 'result' not in self.root_state:
            LOGGER.warning('Have not been processed image')
        else:
            _msg = self.state_message
            self.state_message = 'calc'
            self._sync_state()
            self.root.update()
            threshold = float(self.scale_threshold.get())
            iter_blur = int(self.scale_iter.get())
            save_path = self.current_image_path.split('.')
            save_path[0] += '_floodfill'
            save_path = '.'.join(save_path)
            save_image = ImageCV.run_floodfill(self.image_panel, threshold, iter_blur)
            cv2.imwrite(save_path, save_image)
            self.state_message = _msg
            self._sync_state()
            LOGGER.info('Save file in {}'.format(save_path))
            self.enter_view_mode()

class GraphcutKeyboard(KeyboardHandler, GraphcutViewer):
    def __init__(self):
        super().__init__()

    # press ENTER and switch appication state into EDIT
    @func_profiling
    def enter_edit_mode(self, event=None):
        self.state_message = 'edit'
        self.root_state.append('edit')

        # init tmp panel image
        self.image_panel_tmp.append(self.image_panel.copy())

        # disable detector option
        self.checkbtn_manual_detect.configure(state='disabled')
        self.checkbtn_template_detect.configure(state='disabled')

        # draw symmetric line
        self.symmetric_line = ImageNP.generate_symmetric_line(self.latest_image_panel)

    # press LEFT and move symmetric line to left [step] px
    @func_profiling
    def move_symmetric_to_left(self, event=None, step=1):
        if 'edit' in self.root_state:
            LOGGER.debug('Move symmetric line to left: {}'.format(self.symmetric_line))
            pt1, pt2 = self.symmetric_line
            pt1 = (max(0, pt1[0]-step), pt1[1])
            pt2 = (max(0, pt2[0]-step), pt2[1])
            self.symmetric_line = (pt1, pt2)

    # press RIGHT and move symmetric line to right [step] px
    @func_profiling
    def move_symmetric_to_right(self, event=None, step=1):
        if 'edit' in self.root_state:
            LOGGER.debug('Move symmetric line to right: {}'.format(self.symmetric_line))
            bound_h, bound_w, _ = self.latest_image_panel.shape
            pt1, pt2 = self.symmetric_line
            pt1 = (min(bound_w, pt1[0]+step), pt1[1])
            pt2 = (min(bound_w, pt2[0]+step), pt2[1])
            self.symmetric_line = (pt1, pt2)

if __name__ == '__main__':
    pass
