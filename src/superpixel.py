import cv2
import logging
import numpy as np

from itertools import groupby
from itertools import chain
from skimage.segmentation import slic
from skimage.segmentation import felzenszwalb
from skimage.segmentation import quickshift
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float
from scipy.spatial.distance import cosine


class SuperPixel(object):

    def __init__(self, filename, orig_image=None):
        self.filename = filename

        self.BLUE = [255,0,0]        # rectangle color
        self.RED = [0,0,255]         # PR BG
        self.GREEN = [0,255,0]       # PR FG
        self.BLACK = [0,0,0]         # sure BG
        self.WHITE = [255,255,255]   # sure FG

        # image
        if orig_image is None:
            self.__orig_img = cv2.imread(filename)
        else:
            self.__orig_img = orig_image
        self.__img = self.orig_image
        self.__img_edge = cv2.Canny(self.orig_image, 100, 200)
        self.__img_boundary = self.orig_image
        self.__output = None

        # line
        # self.__h_line = self.calc_h_line()
        self.__mirror_line = self.calc_mirror_line()
        self.__shift_x = None
        self.__shift_y = None

        # point
        self.__ix = None
        self.__iy = None

        # user-defined
        self.__segments = None

    @property
    def orig_image(self):
        return self.__orig_img.copy()

    @property
    def image(self):
        return self.__img

    @property
    def shift_x(self):
        return self.__shift_x

    @shift_x.setter
    def shift_x(self, x):
        self.__shift_x = x

    @property
    def shift_y(self):
        return self.__shift_y

    @shift_y.setter
    def shift_y(self, y):
        self.__shift_y = y

    @property
    def segment(self):
        return self.__segments

    @segment.setter
    def segment(self, segment):
        self.__segments = segment
        self.draw_boundaries()

    @property
    def output(self):
        return self.__output

    @property
    def h_line(self):
        return self.__h_line

    @property
    def mirror_line(self):
        return self.__mirror_line

    def reset(self):
        self.__img = self.__orig_img.copy()
        self.__ix = None
        self.__iy = None

    def calc_h_line(self):
        img = self.__orig_img.copy()
        img = (img > 250).all(axis=2)
        row = int(img.shape[0]/2)
        scan_scale = 10
        result = None

        while True:
            replace_flag = False

            for r in range(row-scan_scale, row+scan_scale):
                group_pixels = [list(g) for k, g in groupby(img[r])]
                key = [k[0] for k in group_pixels]

                if key != [True, False, True]:
                    continue

                if not result or len(group_pixels[1]) < len(result[1][1]):
                    result = (r, group_pixels)
                    replace_flag = True

            if replace_flag:
                row = result[0]
                if 0 > result[0]-scan_scale or result[0]+scan_scale > img.shape[0]:
                    break
            else:
                break

        self.__h_line = ((0, result[0]), (img.shape[1], result[0]))

    def calc_mirror_line(self):
        h, w, _ = self.__orig_img.shape
        line_x = int(w/2)
        approach_x = [line_x]
        scope = 10

        while True:
            max_similarity = None

            for x in range(line_x-scope, line_x+scope):
                min_w = min(x, w-x)
                sim = cosine(
                    self.__orig_img[0:h, x-min_w:x].flatten(),
                    np.fliplr(self.__orig_img[0:h, x:x+min_w].copy()).flatten())

                if max_similarity is None or sim > max_similarity[1]:
                    max_similarity = (x, sim)

            if max_similarity[0] == line_x:
                break
            else:
                line_x = max_similarity[0]

        logging.info('get symetrical line {0}'.format((line_x, h)))
        return ((line_x, 0), (line_x, h))

    def get_all_rect(self):
        rects = []

        if self.__shift_x and self.__shift_y and self.mirror_line:
            h, w, _ = self.__orig_img.shape
            pt1, pt2 = self.mirror_line

            rects = [
                (0, 0, pt1[0]-self.shift_x, self.shift_y),
                (pt2[0]+self.shift_x, 0, w-pt2[0]-self.shift_x, self.shift_y),
                (0, self.shift_y, pt1[0]-self.shift_x, h-self.shift_y),
                (pt2[0]+self.shift_x, self.shift_y, w-pt2[0]-self.shift_x, h-self.shift_y)
            ]

        else:
            logging.warning('No defined symetrical line and rect coordinate')

        return rects

    def draw_boundaries(self):
        self.__img_boundary = mark_boundaries(
            img_as_float(cv2.cvtColor(self.__img_boundary, cv2.COLOR_BGR2RGB)),
            self.__segments,
            color=self.BLACK
            )
        self.__img_boundary = self.__img_boundary*255
        self.__img_boundary = self.__img_boundary.astype('uint8')
        self.__img_boundary = cv2.cvtColor(self.__img_boundary, cv2.COLOR_RGB2BGR)

    def draw_lines(self, x, y, color, thickness):
        h, w, channels = self.__orig_img.shape
        pt1, pt2 = self.mirror_line
        shift = abs(x - pt1[0])
        cv2.line(self.__img, (pt1[0]+shift, 0), (pt2[0]+shift, pt2[1]), color, thickness)
        cv2.line(self.__img, (pt1[0]+shift, y), (w, y), color, thickness)
        cv2.line(self.__img, (pt1[0]-shift, 0), (pt2[0]-shift, pt2[1]), color, thickness)
        cv2.line(self.__img, (pt1[0]-shift, y), (0, y), color, thickness)

    def onmouse(self, event, x, y, flags, params):

        # draw line
        if event == cv2.EVENT_MOUSEMOVE:
            self.__img = self.__img_boundary.copy()

            if self.__ix and self.__iy:
                self.draw_lines(self.__ix, self.__iy, self.BLUE, 2)

            pt1, pt2 = self.mirror_line
            cv2.line(self.__img, pt1, pt2, self.BLACK, 3)
            self.draw_lines(x, y, self.RED, 2)

        elif event == cv2.EVENT_LBUTTONUP:
            self.__img = self.__img_boundary.copy()
            pt1, pt2 = self.mirror_line
            cv2.line(self.__img, pt1, pt2, self.BLACK, 3)
            self.draw_lines(x, y, self.BLUE, 2)
            self.__ix = x
            self.__iy = y
            self.__shift_x = abs(self.__mirror_line[0][0]-x)
            self.__shift_y = y

    def active(self, interactive=True):
        logging.debug('image shape (%d, %d, %d)' % self.__img.shape)

        if interactive:
            cv2.namedWindow('input', cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
            cv2.setMouseCallback('input', self.onmouse)
            cv2.moveWindow('input', self.__img.shape[1], 0)
            self.__img = self.__img_boundary.copy()
            cv2.line(self.__img,
                self.mirror_line[0], self.mirror_line[1], self.BLACK, 2)
            # h_pt1, h_pt2 = self.__h_line
            # cv2.line(self.__img, h_pt1, h_pt2, self.BLUE,2)

            while True:
                cv2.imshow('input', self.__img)
                k = cv2.waitKey(1)

                # esc to exit
                if k == 27:
                    break

                # reset everything
                elif k == ord('r'):
                    self.reset()
                    self.__img = self.__img_boundary.copy()
                    cv2.line(self.__img,
                        self.mirror_line[0], self.mirror_line[1], self.BLACK, 2)
                    logging.info(' Reset all actions')

            cv2.destroyAllWindows()

        # merge super pixel to super super pixel in rect
        self.__img = self.__img_boundary.copy()
        cv2.line(self.__img,
            self.mirror_line[0], self.mirror_line[1], self.BLACK, 2)
        rects = self.get_all_rect()
        parts_output = []
        if rects:
            for i, rect in enumerate(rects):
                x, y, w, h = rect
                cv2.rectangle(self.__img, (x,y), (x+w,y+h), self.BLUE, 2)
                seg_in_rect = self.__segments[y:y+h, x:x+w].copy()
                seg_info = np.unique(self.__segments, return_counts=True)
                seg_in_rect_info = np.unique(seg_in_rect, return_counts=True)
                self.__mask = np.in1d(seg_info[0], seg_in_rect_info[0])

                output_index = np.where(
                    seg_in_rect_info[1]/seg_info[1][np.where(self.__mask)] > 0.5)
                output_segments = seg_in_rect_info[0][output_index]

                part = self.__orig_img.copy()
                part[np.where(
                    ~np.in1d(self.__segments, output_segments).reshape(
                            self.__orig_img.shape[0],
                            self.__orig_img.shape[1]))] = 255
                parts_output.append(part)

        # FIXME: defined output format
        self.__output = parts_output
