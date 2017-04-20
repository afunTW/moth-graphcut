import os
import cv2
import logging
import numpy as np

class Grabcut(object):
    '''
    ===============================================================================
    Interactive Image Segmentation using GrabCut algorithm.

    This sample shows interactive image segmentation using grabcut algorithm.

    USAGE:
        python grabcut.py <filename>

    README FIRST:
        Two windows will show up, one for input and one for output.

        At first, in input window, draw a rectangle around the object using
    mouse right button. Then press 'n' to segment the object (once or a few times)
    For any finer touch-ups, you can press any of the keys below and draw lines on
    the areas you want. Then again press 'n' for updating the output.

    Key '0' - To select areas of sure background
    Key '1' - To select areas of sure foreground
    Key '2' - To select areas of probable background
    Key '3' - To select areas of probable foreground

    Key 'n' - To update the segmentation
    Key 'r' - To reset the setup
    Key 's' - To save the results
    ===============================================================================
    '''
    def __init__(self, filename):
        self.filename = filename

        self.BLUE = [255,0,0]        # rectangle color
        self.RED = [0,0,255]         # PR BG
        self.GREEN = [0,255,0]       # PR FG
        self.BLACK = [0,0,0]         # sure BG
        self.WHITE = [255,255,255]   # sure FG

        self.DRAW_BG = {'color' : self.BLACK, 'val' : 0}
        self.DRAW_FG = {'color' : self.WHITE, 'val' : 1}
        self.DRAW_PR_FG = {'color' : self.GREEN, 'val' : 3}
        self.DRAW_PR_BG = {'color' : self.RED, 'val' : 2}

        # flag
        self.__rect = (0,0,1,1)
        self.__drawing = False         # flag for drawing curves
        self.__rectangle = False       # flag for drawing rect
        self.__rect_over = False       # flag to check if rect drawn
        self.__rect_or_mask = 100      # flag for selecting rect or mask mode
        self.__value = self.DRAW_FG         # drawing initialized to FG
        self.__thickness = 3           # brush thickness
        self.__ix = None
        self.__iy = None

        # FIXME: prompt image info and get exception
        self.__img = cv2.imread(filename)
        self.__orig_img = self.__img.copy()
        self.__mask = np.zeros(self.__img.shape[:2], dtype=np.uint8)
        self.__output = np.zeros(self.__img.shape, dtype=np.uint8)
        self.__mode = cv2.GC_INIT_WITH_RECT
        self.__bgdmodel = np.zeros((1, 65), np.float64)
        self.__fgdmodel = np.zeros((1, 65), np.float64)
        self.__iter_count = 1

        # user-defined
        self.__segment_count = 0
        self.__mask_records = []

    @property
    def orig_image(self):
        return self.__orig_img

    @property
    def image(self):
        return self.__img

    @property
    def mask(self):
        return self.__mask

    @property
    def rect(self):
        return self.__rect

    @rect.setter
    def rect(self, coor):
        assert isinstance(coor, tuple)
        self.__rect = coor

    @property
    def output(self):
        return self.__output

    @property
    def segment_count(self):
        return self.__segment_count

    @segment_count.setter
    def segment_count(self, count):
        assert isinstance(count, int)
        self.__segment_count = count

    @property
    def mask_records(self):
        return self.__mask_records

    @mask_records.setter
    def mask_records(self, records):
        assert isinstance(records, list)
        self.__mask_records = records

    def reset(self):
        self.__rect = (0,0,1,1)
        self.__drawing = False
        self.__rectangle = False
        self.__rect_over = False
        self.__rect_or_mask = 100
        self.__value = self.DRAW_FG
        self.__thickness = 3
        self.__ix = None
        self.__iy = None
        self.__img = self.__orig_img.copy()
        self.__mask = np.zeros(self.__img.shape[:2], dtype=np.uint8)
        self.__output = np.zeros(self.__img.shape, dtype=np.uint8)
        self.__mode = cv2.GC_INIT_WITH_RECT
        self.__segment_count = 0
        self.__mask_records = []

    def draw_rect(self, x, y):
        assert self.__ix and self.__iy
        cv2.rectangle(
            self.__img,
            (self.__ix, self.__iy), (x, y),
            self.BLUE, 2
        )
        self.__rect = self.get_rect_shape(x, y)
        self.__rect_or_mask = 0

    def draw_circle(self, x, y):
        cv2.circle(
            self.__img, (x, y),
            self.__thickness, self.__value['color'], -1)
        cv2.circle(
            self.__mask, (x, y),
            self.__thickness, self.__value['val'], -1)

    def get_rect_shape(self, x, y):
        assert self.__ix and self.__iy
        return (
            min(self.__ix, x), min(self.__iy, y),
            abs(self.__ix-x), abs(self.__iy-y)
        )

    def onmouse(self, event, x, y, flags, params):

        # draw rectangle
        if event == cv2.EVENT_RBUTTONDOWN:
            self.__rectangle = True
            self.__ix, self.__iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.__rectangle:
                self.__img = self.__orig_img.copy()
                self.draw_rect(x, y)

        elif event == cv2.EVENT_RBUTTONUP:
            self.__rectangle = False
            self.__rect_over = True
            self.draw_rect(x, y)
            logging.debug('Set rectangle (%d, %d, %d, %d)' % self.__rect)
            logging.info(' Now press the key "n" a few times until no further change')

        mask_record = {
            'value': self.__value,
            'coordinate': None,
            'thickness': self.__thickness
        }

        # draw touchup curves
        if event == cv2.EVENT_LBUTTONDOWN:
            if not self.__rect_over:
                logging.warning('first draw rectangle')
            else:
                self.__drawing = True
                self.draw_circle(x, y)
                mask_record['coordinate'] = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.__drawing:
                self.draw_circle(x, y)
                mask_record['coordinate'] = (x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            if self.__drawing:
                self.__drawing = False
                self.draw_circle(x, y)
                mask_record['coordinate'] = (x, y)

        if mask_record['coordinate']:
            self.__mask_records.append(mask_record)

        if event == cv2.EVENT_MOUSEWHEEL:
            if flags > 0:
                self.__thickness += 1
            else:
                self.__thickness -= 1

    def active(self):
        print(self.__doc__)

        self.reset()
        logging.debug('image shape (%d, %d, %d)' % self.__img.shape)

        cv2.namedWindow('output')
        cv2.namedWindow('input', cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback('input', self.onmouse)
        cv2.moveWindow('input', self.__img.shape[1], 0)
        cv2.imshow('input', self.__img)

        while True:
            cv2.imshow('input', self.__img)
            cv2.imshow('output', self.__output)
            k = cv2.waitKey(1)

            # esc to exit
            if k == 27:
                break

            # BG drawing
            elif k == ord('0'):
                logging.info(' mark background regions with left mouse button')
                self.__value = self.DRAW_BG

            # FG drawing
            elif k == ord('1'):
                logging.info(' mark foreground regions with left mouse button')
                self.__value = self.DRAW_FG

            # PR_BG drawing
            elif k == ord('2'):
                logging.info(' mark probable background regions with left mouse button')
                self.__value = self.DRAW_PR_BG

            # PR_FG drawing
            elif k == ord('3'):
                logging.info(' mark probable foreground regions with left mouse button')
                self.__value = self.DRAW_PR_FG

            # save image
            elif k == ord('s'):
                bar = np.zeros((self.__img.shape[0],5,3),np.uint8)
                res = np.hstack((self.__orig_img, bar, self.__img, bar, self.__output))
                cv2.imwrite(''.join(['grabcut_', self.filename, '.png']), res)
                logging.info(' Result saved as image')

            # reset everything
            elif k == ord('r'):
                self.reset()
                logging.info(' Reset all actions')

            # segment the image
            elif k == ord('n'):

                # grabcut with rect
                if not self.__rect_or_mask:
                    logging.info('grabcut with rectangle')
                    self.__mode = cv2.GC_INIT_WITH_RECT
                    self.__rect_or_mask = 1

                # grabcut with mask
                elif self.__rect_or_mask:
                    logging.info('grabcut with mask')
                    self.__mode = cv2.GC_INIT_WITH_MASK

                self.__segment_count += self.__iter_count
                cv2.grabCut(
                    self.__orig_img,
                    self.__mask,
                    self.__rect,
                    self.__bgdmodel,
                    self.__fgdmodel,
                    self.__iter_count,
                    self.__mode
                )

            mask2 = np.where(
                (self.__mask == 1) + (self.__mask == 3), 255, 0
            ).astype('uint8')

            self.__output = cv2.bitwise_and(
                self.__orig_img,
                self.__orig_img,
                mask=mask2
            )

        cv2.destroyAllWindows()

    def simulate(self):
        assert self.__rect and self.__segment_count
        logging.debug('image shape (%d, %d, %d)' % self.__img.shape)
        logging.debug('grabcut with rectangle (%d, %d, %d, %d)' % self.__rect)

        ix, iy, w, h = self.__rect
        self.__mode = cv2.GC_INIT_WITH_RECT
        self.__ix, self.__iy = ix, iy
        self.draw_rect(ix+w, iy+h)
        cv2.grabCut(
            self.__orig_img,
            self.__mask,
            self.__rect,
            self.__bgdmodel,
            self.__fgdmodel,
            self.__iter_count,
            self.__mode
            )

        logging.debug('grabcut with mask %d times' % (self.__segment_count))
        self.__mode = cv2.GC_INIT_WITH_MASK

        for record in self.__mask_records:
            self.__value = record['value']
            self.__thickness = record['thickness']
            self.draw_circle(record['coordinate'][0], record['coordinate'][1])

        for _ in range(self.__segment_count-1):
            cv2.grabCut(
                self.__orig_img,
                self.__mask,
                self.__rect,
                self.__bgdmodel,
                self.__fgdmodel,
                self.__iter_count,
                self.__mode
                )

        mask2 = np.where(
            (self.__mask == 1) + (self.__mask == 3), 255, 0
        ).astype('uint8')

        self.__output = cv2.bitwise_and(
            self.__orig_img,
            self.__orig_img,
            mask=mask2
        )
