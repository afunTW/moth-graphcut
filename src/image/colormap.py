"""
heatmap.py
    [class] HeatMap: define a heat map for transformation and operation
"""
import logging

import numpy as np

from .color import ColorTransformation as c_trans
from .color import Palette

LOGGER = logging.getLogger(__name__)

class ColorMap(object):
    """
    Input and matrix in float and out put as image

    [Input] ndarray
    [Output] ndarray
    """
    def __init__(self, mat):
        self.mat = mat
        self.mat_row, self.mat_col = len(mat), len(mat[0])
        self.palette = Palette()
        self._min_value = min(min(t for t in row) for row in mat)
        self._max_value = max(max(t for t in row) for row in mat)

    @property
    def min_value(self):
        return self._min_value

    @property
    def max_value(self):
        return self._max_value

    def transform_to_rgb(self):
        rgb_mat = []
        for row in self.mat:
            rgb_row = [
                list(c_trans.color_transformation(
                    col, self._min_value, self._max_value, self.palette.temperature_rgb))
                for col in row
            ]
            rgb_mat.append(rgb_row)
        return np.array(rgb_mat)

    def transform_to_gray(self):
        gray_mat = []
        for row in self.mat:
            gray_row = [
                c_trans.gray_transformation(
                    col, self._min_value, self._max_value, self.palette.grayscale)
                for col in row
            ]
            gray_mat.append(gray_row)
        return np.array(gray_mat)
