import cv2
import logging
import imutils
import numpy as np


class ShapeDetector(object):
    def __init__(self, template, target):
        # const
        self.BLUE = [255,0,0]        # rectangle color
        self.RED = [0,0,255]         # PR BG
        self.GREEN = [0,255,0]       # PR FG
        self.BLACK = [0,0,0]         # sure BG
        self.WHITE = [255,255,255]   # sure FG
        self.methods = [cv2.TM_CCOEFF,cv2.TM_CCOEFF_NORMED,cv2.TM_CCORR,
        cv2.TM_CCORR_NORMED,cv2.TM_SQDIFF,cv2.TM_SQDIFF_NORMED]

        # image
        self.__template = cv2.imread(template)
        self.__template = cv2.cvtColor(self.__template, cv2.COLOR_BGR2GRAY)
        self.__template = cv2.Canny(self.__template, 50, 100)
        self.__target_img = cv2.imread(target)
        self.__target_img = cv2.cvtColor(self.__target_img, cv2.COLOR_BGR2GRAY)
        self.__output = cv2.imread(target)

        # flag
        self.__found = None

    @property
    def output(self):
        return self.__output

    def detect(self, method=cv2.TM_CCOEFF, show=False):

        # multiscale
        for scale in np.linspace(0.5, 1.0, 20)[::-1]:
            tH, tW = self.__template.shape
            img_w = self.__target_img.shape[1]
            resized_img = imutils.resize(self.__target_img, width=int(img_w*scale))
            ratio = img_w / float(resized_img.shape[1])

            if resized_img.shape[0] < tH or resized_img.shape[1] < tW:
                break

            target_edge = cv2.Canny(resized_img, 50, 200)
            match_result = cv2.matchTemplate(target_edge, self.__template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_result)

            # get the maximum correlation value
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                if self.__found is None or min_val < self.__found[0]:
                    self.__found = (min_val, min_loc, ratio)
            else:
                if self.__found is None or max_val > self.__found[0]:
                    self.__found = (max_val, max_loc, ratio)

            if show:
                val, loc, r = self.__found
                top_left = (int(loc[0]*r), int(loc[1]*r))
                bottom_right = (int((loc[0]+tW)*r), int((loc[1]+tH)*r))
                resized_img = cv2.cvtColor(resized_img, cv2.COLOR_GRAY2BGR)
                cv2.rectangle(resized_img, top_left, bottom_right, self.BLUE, 2)
                cv2.imshow('matching', resized_img)
                cv2.waitKey(0)

        val, loc, r = self.__found
        top_left = (int(loc[0]*r), int(loc[1]*r))
        bottom_right = (int((loc[0]+tW)*r), int((loc[1]+tH)*r))
        cv2.rectangle(self.output, top_left, bottom_right, self.BLUE, 2)
        cv2.imshow('output', self.output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
