"""
Based on src.view.template.MothGraphCutViewer() to bind the action and widget
"""
import logging
import sys

import cv2

sys.path.append('../..')
from src import tkconfig
from src.actions.detector import TemplateDetector
from src.actions.keyboard import GraphcutKeyboard, PreprocessKeyboard
from src.actions.mouse import GraphcutMouse, PreprocessMouse

LOGGER = logging.getLogger(__name__)
STATE_MANUAL_DETECT = 'manual'
STATE_AUTO_DETECT = 'auto'

class MothPreprocessAction(PreprocessKeyboard, PreprocessMouse):
    def __init__(self):
        super().__init__()

        # default binding
        self.root.bind(tkconfig.KEY_UP, self.switch_to_previous_image)
        self.root.bind(tkconfig.KEY_DOWN, self.switch_to_next_image)
        self.root.bind(tkconfig.KEY_ESC, self.enter_view_mode)
        self.root.bind(tkconfig.KEY_ENTER,
                       lambda x: self.enter_edit_mode(x,
                                                      self.meta_floodfill_threshold,
                                                      self.meta_floodfill_iter))

        # widget default binding
        self._sync_floodfill_option()

    @property
    def meta_floodfill_threshold(self):
        return self.scale_threshold.get()

    @property
    def meta_floodfill_iter(self):
        return int(self.scale_iter.get())

    # sync and detect whether value changes to re-render the floodfill
    def _sync_floodfill_option(self):
        self.scale_iter.bind(tkconfig.MOUSE_MOTION, self.render_integer_value)

        if 'edit' in self.root_state:
            self.scale_threshold.bind(tkconfig.MOUSE_RELEASE_LEFT, self.render_display)
            self.scale_iter.bind(tkconfig.MOUSE_RELEASE_LEFT, self.render_display)
        else:
            self.scale_threshold.unbind(tkconfig.MOUSE_RELEASE_LEFT)
            self.scale_iter.unbind(tkconfig.MOUSE_RELEASE_LEFT)

        self.root.after(10, self._sync_floodfill_option)

class MothGraphcutAction(GraphcutKeyboard, GraphcutMouse):
    def __init__(self):
        super().__init__()

        # default binding
        self.root.bind(tkconfig.KEY_UP, self.switch_to_previous_image)
        self.root.bind(tkconfig.KEY_DOWN, self.switch_to_next_image)
        self.root.bind(tkconfig.KEY_ENTER, self.enter_edit_mode)
        self._sync_panel_mouse_event()

        # default binding: detector
        self.checkbtn_manual_detect.configure(command=self._invoke_manual_detect)
        self.checkbtn_template_detect.configure(command=self._invoke_template_detect)
        self._sync_detection()

    # unique the element in list
    def _unique(self, l):
        return list(set(l))

    # render manual detector option
    def _invoke_manual_detect(self):
        if self.checkbtn_manual_detect.instate(['selected']):
            LOGGER.info('detect mode: manual')
            self.val_template_detect.set(False)
            # self._sync_detection()
        elif self.checkbtn_manual_detect.instate(['!selected']):
            self.val_manual_detect.set(False)

    # render template detector option
    def _invoke_template_detect(self):
        if self.checkbtn_template_detect.instate(['selected']):
            LOGGER.info('detect mode: auto')
            self.val_manual_detect.set(False)
            # self._sync_detection()
        elif self.checkbtn_template_detect.instate(['!selected']):
            self.val_template_detect.set(False)

    # detect and clear image when detect option was selected
    def _sync_detection(self):
        in_manual = self.checkbtn_manual_detect.instate(['selected'])
        in_template = self.checkbtn_template_detect.instate(['selected'])
        is_manual = not in_template and in_manual
        is_template = not in_manual and in_template
        is_detected = (STATE_MANUAL_DETECT in self.panel_image_state or
                       STATE_AUTO_DETECT in self.panel_image_state)
        nor_detection = not in_manual and not in_template

        if self.detector is None and self.image_template is not None:
            self._init_detector()

        if is_template and STATE_AUTO_DETECT not in self.panel_image_state:
            if STATE_MANUAL_DETECT in self.panel_image_state:
                self.panel_image_state.remove(STATE_MANUAL_DETECT)

            target_h, target_w, _ = self.image_panel.shape
            x, y, w, h = self.detector.detect_template()
            self.image_panel[y:y+h, x:x+w, :] = 255

            possible_rects = self.detector.detect_rectangle((0, y, target_w, target_h-y))
            for rect in possible_rects:
                _x, _y, _w, _h = rect
                self.image_panel[_y:_y+_h, _x:_x+_w, :] = 255
            self.panel_image_state.append(STATE_AUTO_DETECT)

            # # DEBUG MODE: visualize
            # cv2.rectangle(self.image_panel, (x, y), (x+w, y+h), (0,0,255),2)
            # for rect in possible_rects:
            #     _x, _y, _w, _h = rect
            #     cv2.rectangle(self.image_panel, (_x, _y), (_x+_w, _y+_h), (255,0,0),2)

            self._update_image()
            LOGGER.info('In template detection, current state: {}'.format(
                self.panel_image_state
            ))

        elif is_manual and STATE_MANUAL_DETECT not in self.panel_image_state:
            # reset the image_panel then manual clear
            self.image_panel = cv2.imread(self.current_image_path)
            if STATE_AUTO_DETECT in self.panel_image_state:
                self.panel_image_state.remove(STATE_AUTO_DETECT)
            self.panel_image_state.append(STATE_MANUAL_DETECT)
            self._update_image()
            LOGGER.info('In manual detection, current state: {}'.format(
                self.panel_image_state
            ))
            pass

        elif nor_detection and is_detected:
            self.image_panel = cv2.imread(self.current_image_path)
            if STATE_MANUAL_DETECT in self.panel_image_state:
                self.panel_image_state.remove(STATE_MANUAL_DETECT)
            if STATE_AUTO_DETECT in self.panel_image_state:
                self.panel_image_state.remove(STATE_AUTO_DETECT)
            self._update_image()
            LOGGER.info('Reset, current state: {}'.format(
                self.panel_image_state
            ))

        self.root.after(100, self._sync_detection)

    # determine the mouse event in each state
    def _sync_panel_mouse_event(self):
        # edit mode
        if 'edit' in self.root_state:
            self.root.bind(tkconfig.KEY_LEFT, self.move_symmetric_to_left)
            self.root.bind(tkconfig.KEY_RIGHT, self.move_symmetric_to_right)
            self.label_panel_image.bind(tkconfig.MOUSE_MOTION, self.draw_symmetric_line)

        self.root_state = self._unique(self.root_state)
        self.root.after(100, self._sync_panel_mouse_event)

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
    THERMAL = path.abspath('../../image/thermal/original_rgb/')

    if not path.exists(THERMAL):
        import zipfile
        with zipfile.ZipFile(path.abspath('../../image/thermal.zip'), 'r') as zip_ref:
            zip_ref.extractall(path.abspath('../../image'))

    SAMPLE_IMGS = sorted([i for i in glob(path.join(SAMPLE, '*.jpg'))])
    THERMAL_IMGS = sorted([i for i in glob(path.join(THERMAL, '*.jpg'))])

    preprocess_action = MothPreprocessAction()
    preprocess_action.input_image(*THERMAL_IMGS)
    preprocess_action.mainloop()

    # graphcut_action = MothGraphcutAction()
    # graphcut_action.input_template(TEMPLATE_IMG)
    # graphcut_action.input_image(*SAMPLE_IMGS)
    # graphcut_action.mainloop()
