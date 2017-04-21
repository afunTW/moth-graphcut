import cv2
import logging
import numpy as np

from skimage.segmentation import slic
from skimage.segmentation import felzenszwalb
from skimage.segmentation import quickshift
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float


class SuperPixel(object):
    '''
    ===============================================================================
    Interactive Image Segmentation using superpixel algorithm.

    Key 'n' - To update the segmentation
    Key 'r' - To reset the setup
    ===============================================================================
    '''

    def __init__(self, filename):
        self.filename = filename

        self.BLUE = [255,0,0]        # rectangle color
        self.RED = [0,0,255]         # PR BG
        self.GREEN = [0,255,0]       # PR FG
        self.BLACK = [0,0,0]         # sure BG
        self.WHITE = [255,255,255]   # sure FG

        # image
        self.__orig_img = cv2.imread(filename)
        self.__img = self.__orig_img.copy()
        self.__boundary_img = self.__orig_img.copy()
        self.__output = np.zeros(self.__img.shape, dtype=np.uint8)
        self.__rectangle = False
        self.__rect = (0, 0, 1, 1)
        self.__ix = None
        self.__iy = None
        self.__segments = None
        self.__mask = None

    @property
    def orig_image(self):
        return self.__orig_img.copy()

    @property
    def image(self):
        return self.__img

    @property
    def rect(self):
        return self.__rect

    @rect.setter
    def rect(self, coor):
        assert isinstance(coor, tuple)
        self.__rect = coor

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

    def reset(self):
        self.__img = self.__orig_img.copy()
        self.__boundary_img = self.__orig_img.copy()
        self.__output = np.zeros(self.__img.shape, dtype=np.uint8)
        self.__rectangle = False
        self.__rect = (0, 0, 1, 1)
        self.__ix = None
        self.__iy = None
        # self.__segments = None

    def get_rect_shape(self, x, y):
        assert self.__ix and self.__iy
        return (
            min(self.__ix, x), min(self.__iy, y),
            abs(self.__ix-x), abs(self.__iy-y)
        )

    def draw_rect(self, x, y):
        assert self.__ix and self.__iy
        cv2.rectangle(
            self.__img,
            (self.__ix, self.__iy), (x, y),
            self.BLUE, 2
        )
        self.__rect = self.get_rect_shape(x, y)

    def draw_boundaries(self):
        self.__boundary_img = mark_boundaries(
            img_as_float(cv2.cvtColor(self.__boundary_img, cv2.COLOR_BGR2RGB)),
            self.__segments,
            color=self.BLACK,
            # outline_color=self.BLACK,
            # mode='thick'
            )
        self.__boundary_img = self.__boundary_img*255
        self.__boundary_img = self.__boundary_img.astype('uint8')
        self.__boundary_img = cv2.cvtColor(self.__boundary_img, cv2.COLOR_RGB2BGR)

    def onmouse(self, event, x, y, flags, params):

        # draw rectangle
        if event == cv2.EVENT_RBUTTONDOWN:
            self.__rectangle = True
            self.__ix, self.__iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.__rectangle:
                self.__img = self.__boundary_img.copy()
                self.draw_rect(x, y)

        elif event == cv2.EVENT_RBUTTONUP:
            self.__rectangle = False
            self.__rect_over = True
            self.draw_rect(x, y)
            logging.debug('Set rectangle (%d, %d, %d, %d)' % self.__rect)

    def active(self):
        print(__doc__)
        logging.debug('image shape (%d, %d, %d)' % self.__img.shape)

        cv2.namedWindow('output')
        cv2.namedWindow('input', cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback('input', self.onmouse)
        cv2.moveWindow('input', self.__img.shape[1], 0)
        self.__img = self.__boundary_img.copy()

        while True:
            cv2.imshow('output', self.__output)
            cv2.imshow('input', self.__img)
            k = cv2.waitKey(1)

            # esc to exit
            if k == 27:
                break

            # save image
            elif k == ord('s'):
                bar = np.zeros((self.__img.shape[0],5,3),np.uint8)
                res = np.hstack((self.__orig_img, bar, self.__img, bar, self.__output))
                cv2.imwrite(''.join(['superpixel_', self.filename, '.png']), res)
                logging.info(' Result saved as image')

            # reset everything
            elif k == ord('r'):
                self.reset()
                logging.info(' Reset all actions')

            # merge super pixel to super super pixel in rect
            elif k == ord('n'):
                if self.__rect:
                    x, y, w, h = self.__rect
                    seg_in_rect = self.__segments[y:y+h, x:x+w].copy()
                    seg_info = np.unique(self.__segments, return_counts=True)
                    seg_in_rect_info = np.unique(seg_in_rect, return_counts=True)
                    self.__mask = np.in1d(seg_info[0], seg_in_rect_info[0])

                    output_index = np.where(
                        seg_in_rect_info[1]/seg_info[1][np.where(self.__mask)] > 0.5)
                    output_segments = seg_in_rect_info[0][output_index]

                    self.__output = self.__orig_img.copy()
                    self.__output[np.where(
                        ~np.in1d(
                            self.__segments, output_segments
                            ).reshape(
                                self.__orig_img.shape[0],
                                self.__orig_img.shape[1]))] = 255
