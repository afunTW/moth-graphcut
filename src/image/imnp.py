"""
Using Numpy to handle the Image operation
"""
import logging
import sys

import numpy as np
from scipy.spatial.distance import cosine

sys.path.append('../..')
from src.support.profiling import func_profiling

LOGGER = logging.getLogger(__name__)

class ImageNP(object):
    def __init__(self):
        super().__init__()

    @staticmethod
    @func_profiling
    def generate_checkboard(shape, block_size=10, color=125):
        """generate transparents-like background"""
        im = np.zeros(shape) * 255

        for i in range(block_size):
            for j in range(block_size):
                im[i::block_size*2, j::block_size*2] = color
                im[i+block_size::block_size*2, j+block_size::block_size*2] = color

        return im

    @staticmethod
    @func_profiling
    def generate_symmetric_line(image, interval=10):
        """generate symmetric line of image"""
        try:
            h, w, channel = image.shape
        except Exception as identifier:
            LOGGER.error(identifier)
            return
        line_x = int(w/2)
        approach_x = [line_x]

        while True:
            max_similarity = None

            for x in range(line_x-interval, line_x+interval):
                min_w = min(x, w-x)
                sim = cosine(
                   image[0:h, x-min_w:x].flatten(),
                    np.fliplr(image[0:h, x:x+min_w].copy()).flatten())

                if max_similarity is None:
                    max_similarity = (x, sim)
                elif sim > max_similarity[1]:
                    max_similarity = (x, sim)

            if max_similarity[0] == line_x:
                break
            else:
                line_x = max_similarity[0]

        line_ptxs = ((line_x, 0), (line_x, h))
        LOGGER.debug('Generate symmetric line {}'.format(line_ptxs))
        return line_ptxs

    @staticmethod
    @func_profiling
    def shift_matrix(x, y, mat, threshold=255):
        coor = np.argwhere(mat == threshold).transpose()
        col, row = coor[0], coor[1]
        row_shift, col_shift = row-x, col-y
        return col_shift, row_shift

    @staticmethod
    @func_profiling
    def coor_to_contour(coor):
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

    @staticmethod
    @func_profiling
    def contour_to_coor(contour):
        coor = contour.reshape(contour.shape[0], 2)
        coor = coor.transpose()
        coor = coor.tolist()
        coor = [np.array(i) for i in coor]
        coor.reverse()
        coor = tuple(coor)
        return coor

    @staticmethod
    @func_profiling
    def interpolation_ptx(block):
        block = sorted(block, key=lambda ptx: ptx[0])
        xp = [p[0] for p in block]
        fp = [p[1] for p in block]

        track = [(
            int(x), int(np.interp(x, xp, fp))
            ) for x in range(min(xp), max(xp)+1)]

        return track

if __name__ == '__main__':
    """testing"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
    im = ImageNP.generate_checkboard((533,800,3), block_size=5)
