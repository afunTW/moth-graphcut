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

        # default binding: detector
        self.checkbtn_manual_detect.configure(command=self._invoke_manual_detect)
        self.checkbtn_template_detect.configure(command=self._invoke_template_detect)

    # invoke the callback when the manual detection checkbutton changed state
    def _invoke_manual_detect(self):
        if self.checkbtn_manual_detect.instate(['selected']):
            self.val_template_detect.set(False)
        elif self.checkbtn_manual_detect.instate(['!selected']):
            pass

    # invoke the callback when the template detection checkbutton changed state
    def _invoke_template_detect(self):
        if self.checkbtn_template_detect.instate(['selected']):
            self.val_manual_detect.set(False)
        elif self.checkbtn_template_detect.instate(['!selected']):
            pass

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
    TEMPLATE_IMG = path.abspath('../../image/10mm.png')
    SAMPLE = path.abspath('../../image/sample/')
    SAMPLE_IMGS = sorted([i for i in glob(path.join(SAMPLE, '*.jpg'))])

    action = MothActionsTemplate()
    action.input_template(TEMPLATE_IMG)
    action.input_image(*SAMPLE_IMGS)
    action.mainloop()
