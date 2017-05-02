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
        self.__template_rect = None
        self.__rect = []

        # flag
        self.__found = None

    @property
    def output(self):
        return self.__output

    @property
    def rectangles(self):
        return self.__rect

    @property
    def template_result(self):
        if self.__found:
            return self.__template_rect
        else:
            return None

    @classmethod
    def points2rect(self, pos1, pos2):
        x = min(pos1[0], pos2[0])
        y = min(pos1[1], pos2[1])
        w = abs(pos1[0] - pos2[0])
        h = abs(pos1[1] - pos2[1])
        return (x, y, w, h)

    def detect_template(self, method=cv2.TM_CCOEFF, show=False):
        self.__found = None

        # multiscale
        for scale in np.linspace(0.5, 1.0, 32)[::-1]:
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

        val, loc, r = self.__found
        top_left = (int(loc[0]*r), int(loc[1]*r))
        bottom_right = (int((loc[0]+tW)*r), int((loc[1]+tH)*r))
        self.__template_rect = self.points2rect(top_left, bottom_right)

        if show:
            output = self.output.copy()
            cv2.rectangle(output, top_left, bottom_right, self.RED, 2)
            cv2.imshow('output', output)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    def detect_retangle(self, focus_rect=None):
        target = self.__target_img.copy()
        target[np.where(target > [5])] = 120
        # target_blur = cv2.GaussianBlur(target, (5,5), 0)
        # target_thresh = cv2.threshold(target_blur, 60, 255, cv2.THRESH_BINARY)[1]
        target_thresh = cv2.threshold(target, 60, 255, cv2.THRESH_BINARY)[1]
        cnts = cv2.findContours(target_thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[1]

        for i, c in enumerate(cnts):
            perimeter = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.003*perimeter, True)
            x, y, w, h = cv2.boundingRect(approx)

            if focus_rect:
                assert isinstance(focus_rect, tuple) and len(focus_rect) == 4
                X, Y, W, H = focus_rect

                if X<x<x+w<X+W and Y<y<y+h<Y+H:
                    self.__rect.append((x, y, w, h))
