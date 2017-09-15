"""
Defined callback functions of keyboard event
"""
import logging
import sys

sys.path.append('../')
from src.view.template import MothViewerTemplate
from src.support.profiling import func_profiling

LOGGER = logging.getLogger(__name__)

class MothKeyboardHandler(MothViewerTemplate):
    def __init__(self):
        super().__init__()

    # press UP and switch to previous image in image queue
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
                self.current_image_path = self.image_queue[max(0, current_index-step)]
                LOGGER.info('({}/{}) Ready to process image {}'.format(
                    current_index+1, len(self.image_queue), self.current_image_path
                ))
                self._update_image(self.current_image_path)
        else:
            LOGGER.warning('No given image')

    # press DOWN and switch to next image in image queue
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
                self.current_image_path = self.image_queue[min(current_index+step, len(self.image_queue)-1)]
                LOGGER.info('({}/{}) Ready to process image {}'.format(
                    current_index+1, len(self.image_queue), self.current_image_path
                ))
                self._update_image(self.current_image_path)
        else:
            LOGGER.warning('No given image')

if __name__ == '__main__':
    pass