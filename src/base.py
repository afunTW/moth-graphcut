import os
import cv2
import logging
import numpy as np

from src.color import RGB
from src.keyboard import KeyHandler
from src.msg_box import MessageBox
from src.msg_box import Instruction
from scipy.spatial.distance import cosine


class BaseImage(object):
    def __init__(self):
        super().__init__()

    def generate_transparent(self, shape, n=10, color=125):
        '''
        generate transparents background
        '''
        img = np.zeros(shape) * 255

        for i in range(n):
            for j in range(n):
                img[i::n*2, j::n*2] = color
                img[i+n::n*2, j+n::n*2] = color

        return img

    def generate_mirror_line(self, image, scope=10):
        '''
        generate mirror line
        '''
        img = image.copy()
        h, w, _ = img.shape
        line_x = int(w/2)
        approach_x = [line_x]

        while True:
            max_similarity = None

            for x in range(line_x-scope, line_x+scope):
                min_w = min(x, w-x)
                sim = cosine(
                   img[0:h, x-min_w:x].flatten(),
                    np.fliplr(img[0:h, x:x+min_w].copy()).flatten())

                if max_similarity is None or sim > max_similarity[1]:
                    max_similarity = (x, sim)

            if max_similarity[0] == line_x: break
            else: line_x = max_similarity[0]

        logging.info('generate mirror line {0}'.format(((line_x, 0), (line_x, h))))
        return ((line_x, 0), (line_x, h))

    def filled_component(self, img, contour, threshold=255):
        cmp_img = np.zeros_like(img)
        cmp_img[contour] = img[contour]
        cmp_img = cv2.cvtColor(cmp_img, cv2.COLOR_BGR2GRAY)
        cmp_img, cnt, hierarchy = cv2.findContours(
            cmp_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cmp_img = np.zeros_like(cmp_img)
        cv2.drawContours(cmp_img, cnt, -1, threshold, -1)
        return cmp_img, cnt

    def matrix_shifting(self, x, y, mat, threshold=255):
        coor = np.argwhere(mat == threshold).transpose()
        col, row = coor[0], coor[1]
        row_shift, col_shift = row-x, col-y
        return col_shift, row_shift

    def coor_to_contour(self, coor):
        '''
        coor = (array([y_axis], array([x_axis])
        contour = array([
            [[x1, y1]],
            [[x2, y2]],
            ...
        ], dtype='int32')
        '''
        cnt = list(coor)
        cnt.reverse()
        cnt = np.array(cnt)
        cnt = cnt.transpose()
        cnt = cnt.reshape((cnt.shape[0], 1, 2))
        cnt = cnt.astype('int32')
        return cnt

    def contour_to_coor(self, contour):
        coor = contour.reshape(contour.shape[0], 2)
        coor = coor.transpose()
        coor = coor.tolist()
        coor = [np.array(i) for i in coor]
        coor.reverse()
        coor = tuple(coor)
        return coor

    def get_interp_ptx(self, block):
        block = sorted(block, key=lambda ptx: ptx[0])
        xp = [p[0] for p in block]
        fp = [p[1] for p in block]

        track = [(
            int(x), int(np.interp(x, xp, fp))
            ) for x in range(min(xp), max(xp)+1)]

        return track

    def get_component_by(self, threshold, nth, by):
        '''
        return nth connected component by the value in stat matrix
        in descending sequences
            cv2.CC_STAT_LEFT The leftmost (x) coordinate
            cv2.CC_STAT_TOP The topmost (y) coordinate
            cv2.CC_STAT_WIDTH The horizontal size of the bounding box
            cv2.CC_STAT_HEIGHT The vertical size of the bounding box
            cv2.CC_STAT_AREA The total area (in pixels) of the connected component
        '''
        output = cv2.connectedComponentsWithStats(threshold, 4, cv2.CV_32S)
        assert by in [
            cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP,
            cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT, cv2.CC_STAT_AREA]
        if 0 >= nth or nth >= output[0]: return

        cond_sequence = [(i ,output[2][i][by]) for i in range(output[0]) if i != 0]
        cond_sequence = sorted(cond_sequence, key=lambda x: x[1], reverse=True)
        return np.where(output[1] == cond_sequence[nth-1][0])

    def get_rgba_component(self, image, mask):
        if mask is None: return None
        _mask = mask/255
        _mask = np.expand_dims(_mask, axis = 2)
        _mask = np.concatenate((_mask, _mask, _mask), axis = 2)
        image = np.multiply(image, _mask).astype('uint8')
        b, g, r = cv2.split(image)
        return cv2.merge((b, g, r, mask))

class BaseCV(object):
    def __init__(self):
        super().__init__()

    @classmethod
    def draw_line_by_track(cls, image, src, value):
        for i, ptx in enumerate(src):
            if i == 0: continue
            cv2.line(image, src[i-1], src[i], value, 2)
        return image

    @classmethod
    def draw_line_by_block(cls, image, src, value):
        for block in src:
            image = BaseCV.draw_line_by_track(image, block, value)
        return image

class BaseGraphCut(RGB, KeyHandler, BaseImage, BaseCV):
    def __init__(self, filename, image=None):
        super().__init__()
        self.filename = filename
        self.instruction = Instruction()

        self.CLEAR_UPWARD = {'color': self.BLACK}
        self.CLEAR_DOWNWARD = {'color': self.BLACK}
        self.LEFT = 'left'
        self.RIGHT = 'right'
        self.STATE = 'none'
        self.ACTION = 'save'
        self.THRESHOLD = 250

    def null_callback(self, value):
        pass

    def ask_to_save(self):
        MBox = MessageBox()
        want_save = MBox.ask_ques()
        return want_save
