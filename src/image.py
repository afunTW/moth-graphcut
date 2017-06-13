import numpy as np

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
