import os
import logging

import numpy as np

import cv2
from skimage import measure

LOGGER = logging.getLogger(__name__)

class AlignmentCore(object):
    def __init__(self, img_path, heat_dirpath, avg_nth_img=30):
        self.img_path = img_path
        self.heat_dirpath = heat_dirpath
        self.avg_nth_img = avg_nth_img
        self.transform_matrix = None
        self.result_img = None

    # handle the image path and reading
    def _load_image(self):
        self.heat_path = [os.path.join(self.heat_dirpath, i) for i in os.listdir(self.heat_dirpath)]
        self.heat_path = sorted(self.heat_path, key=lambda x: int(x.split(os.sep)[-1].split('_')[-1].split('.')[0]))
        heat_img = self.heat_path[0]
        mask_img = self.heat_path[74]

        # original image should resize to heat image size
        self.original_img = cv2.imread(self.img_path)
        self.heat_img = cv2.imread(heat_img, cv2.IMREAD_GRAYSCALE)
        self.mask_img = cv2.imread(mask_img, cv2.IMREAD_GRAYSCALE)

    # preprocess the original, heat, and mask image
    def _preprocess_image(self):
        # original image should resize to thermal image size
        self.original_img = cv2.resize(self.original_img, (self.heat_img.shape[1], self.heat_img.shape[0]))

        # preprocess heat image to get the transform matrix
        self.heat_img = np.zeros((self.heat_img.shape[1], self.heat_img.shape[0], self.avg_nth_img))
        self.heat_img = self.heat_img.astype('float32')
        self.heat_img = self._avg_sample_image(self.heat_img, self.heat_path[1:self.avg_nth_img+1])
        self.heat_img = np.sum(self.heat_img, axis=2)
        self.heat_img = self._normalize_image(self.heat_img)

    # averaging n images
    def _avg_sample_image(self, base, img_path):
        for i, imfile in enumerate(img_path):
            base[:, :, i-1] = cv2.imread(imfile, cv2.IMREAD_GRAYSCALE).astype('float32')
        return base

    # normalize each pixel
    def _normalize_image(self, img):
        img += max(-img.min(), 0)
        img /= img.max()
        img *= 255
        img = img.astype('uint8')
        return img

    # get contour centers
    def _get_contour_centers(self, img):
        _, contours, _ = cv2.findContours(img.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_L1)
        centres = []

        for i, cnt in enumerate(contours):
            moments = cv2.moments(cnt)
            if moments['m00'] == 0:
                continue

            moment = (int(moments['m10']/moments['m00']), int(moments['m01']/moments['m00']))
            centres.append(moment)

        return centres

    # get nearest centers
    def _get_nearest_centers(self, img, neighbors=8):
        labels = measure.label(img, neighbors=neighbors, background=0)
        centres = []

        for label in np.unique(labels):
            if label == 0:
                 continue

            label_points = np.where(labels == label)

            if len(label_points[0]) < 2:
                continue

            y_center = (label_points[0].min()+label_points[0].max()) // 2
            x_center = (label_points[1].min()+label_points[1].max()) // 2
            center = (x_center ,y_center)
            centres.append(center)

        return centres

    # find max point
    def _find_max_point(self, points):
        lt, lb, rt, rb = {}, {}, {}, {}

        for point in points:
            lt[point] = (-point[0]) + (-point[1])
            lb[point] = (-point[0]) + (point[1])
            rt[point] = (point[0]) + (-point[1])
            rb[point] = (point[0]) + (point[1])

        lt = max(lt, key=lt.get)
        lb = max(lb, key=lb.get)
        rt = max(rt, key=rt.get)
        rb = max(rb, key=rb.get)

        return np.array([lt, lb, rt, rb])

    # find min point
    def _find_min_point(self, points, center):
        lt, lb, rt, rb = {}, {}, {}, {}

        for point in points:
            if point[0] < center[0] and point[1] < center[1]:
                lt[point] = (-point[0]) + (-point[1])
            elif point[0] < center[0] and point[1] >= center[1]:
                lb[point] = (-point[0]) + (point[1])
            elif point[0] >= center[0] and point[1] < center[1]:
                rt[point] = (point[0]) + (-point[1])
            elif point[0] >= center[0] and point[1] >= center[1]:
                rb[point] = (point[0]) + (point[1])

        lt = min(lt, key=lt.get)
        lb = min(lb, key=lb.get)
        rt = min(rt, key=rt.get)
        rb = min(rb, key=rb.get)

        return np.array([lt, lb, rt, rb])

    # find transform matrix
    def _find_transform_matrix(self, orig_img, heat_img, mask_img):

        orig = orig_img.copy()
        heat = heat_img.copy()
        mask = mask_img.copy()

        # original image
        orig = cv2.cvtColor(orig, cv2.COLOR_BGR2HSV)[:, :, 2]
        ret, orig = cv2.threshold(orig, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        if orig[0,:].sum() > 255*5:
            orig = cv2.bitwise_not(orig)

        # mask
        ret, mask = cv2.threshold(mask,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        mask_points = np.where(mask == 255)
        mask_y = (mask_points[0].min(),mask_points[0].max(),(mask_points[0].min()+mask_points[0].max())//2)
        mask_x = (mask_points[1].min(),mask_points[1].max(),(mask_points[1].min()+mask_points[1].max())//2)

        if mask[0, :].sum() > 255*15:
            heat = mask_img.copy()
            threshold = np.sort(heat, axis=None)[int(heat.size*0.01)]
            ret, heat = cv2.threshold(heat, threshold, 255, cv2.THRESH_BINARY)

            # for background colour mixed black and white
            heat = cv2.bitwise_not(heat)
            heat = cv2.medianBlur(heat, 3, 10)
            orig_centers = get_contour_centers(orig)
            orig_points = find_max_point(orig_centers)
            heat_centers = get_nearest_centers(heat)
            heat_points = find_max_point(heat_centers)

        else:
            threshold = np.sort(heat, axis=None)[int(heat.size*0.04)]
            ret, heat = cv2.threshold(heat, threshold, 255, cv2.THRESH_BINARY)

            # for background colour mixed black and white
            heat = cv2.bitwise_not(heat)
            heat[mask_y[0]:mask_y[1], mask_x[0]:mask_x[1]] = 0
            heat[:, mask_x[2]-40:mask_x[2]+40] = 0
            heat[mask_y[2]-40:mask_y[2]+40, :] = 0

            heat = cv2.medianBlur(heat,3,10)
            orig_centers = get_contour_centers(orig)
            orig_points = find_max_point(orig_centers)
            heat_centers = get_nearest_centers(heat)
            heat_points = find_min_point(heat_centers, (mask_x[2], mask_y[2]))

        M, status = cv2.findHomography(heat_points, orig_points)

        return M

    def run(self):
        self._load_image()
        self._preprocess_image()

        try:
            # get the transform matrix
            self.transform_matrix = self._find_transform_matrix(
                self.original_img, self.heat_img, self.mask_img
            )

            # warp the heat image to fit the original image
            self.result_img = cv2.warpPerspective(
                self.heat_img, self.transform_matrix, self.heat_img.shape[:2][::-1]
            )

            # get mask to check the difference of thermal and original image
            self.mask_img = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2HSV)[:, :, 2]
            ret, self.mask_img = cv2.threshold(self.mask_img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
            if self.mask_img[0, :].sum() > 255*5:
                self.mask_img[self.mask_img == 255] = 100
                self.mask_img[self.mask_img == 0] = 255
                self.mask_img[self.mask_img == 100] = 0
            self.mask_img = self.mask_img.astype('bool')
            self.result_img[self.mask_img] = 0

        except Exception as e:
            LOGGER.exception('Cannot get the transform matrix')

        return self.result_img