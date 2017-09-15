"""
Based on src.view.template.MothViewerTemplate() to bind the action and widget
"""
import logging
import sys

sys.path.append('../..')
from src import tkconfig
from src.actions.keyboard import MothKeyboardHandler
from src.support.profiling import func_profiling

LOGGER = logging.getLogger(__name__)

class MothActionsTemplate(MothKeyboardHandler):
    def __init__(self):
        # default binding
        super().__init__()
        self.root.bind(tkconfig.KEY_UP, self.switch_to_previous_image)
        self.root.bind(tkconfig.KEY_DOWN, self.switch_to_next_image)

if __name__ == '__main__':
    """testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
    from glob import glob
    from inspect import currentframe, getframeinfo
    from os import path
    _FILE = path.abspath(getframeinfo(currentframe()).filename)
    SAMPLE = path.abspath('../../image/sample/')
    SAMPLE_IMGS = sorted([i for i in glob(path.join(SAMPLE, '*.jpg'))])

    action = MothActionsTemplate()
    action.input_image(*SAMPLE_IMGS)
    action.mainloop()
