"""
color.py
    [class] Palette: define the pair of color
    [class] ColorTransformation: transform the value to meaningful color pair
"""
import logging


LOGGER = logging.getLogger(__name__)

class Palette(object):
    """
    Palette
    """
    def __init__(self):
        self._temperature_rgb = None
        self._grayscale = None

    @property
    def temperature_rgb(self):
        """
        From (0, 0, 255) to (255, 0, 0), total 256 segments to present
        TODO: using np.linspace to arrange number scope
        """
        if self._temperature_rgb is None:
            red = [r for r in range(0, 256)]
            green = [g for g in range(0, 255, 2)] + [g for g in range(255, 0, -2)]
            blue = [b for b in range(255, -1, -1)]
            self._temperature_rgb = [(red[i], green[i], blue[i]) for i in range(len(red))]
        return self._temperature_rgb

    @property
    def grayscale(self):
        """from 0 (black) to 255 (white)"""
        if self._grayscale is None:
            self._grayscale = [i for i in range(256)]
        return self._grayscale

class ColorTransformation(object):
    """Color transformation just like color interpolation"""
    @staticmethod
    def color_transformation(value, minval, maxval, palette):
        """Convert value in range minval...maxval to the range 0..max_index"""
        max_index = len(palette)-1
        transform_value = (float(value-minval) / (maxval-minval)) * max_index
        int_value, float_value = divmod(transform_value, 1)
        int_value = int(int_value)

        # Nearest color pair and the difference
        c0r, c0g, c0b = palette[int_value]
        c1r, c1g, c1b = palette[min(int_value+1, max_index)]
        dr, dg, db = c1r-c0r, c1g-c0g, c1b-c0b

        return c0r+float_value*dr, c0g+float_value*dg, c0b+float_value*db

    @staticmethod
    def gray_transformation(value, minval, maxval, palette):
        """Covert value to gray"""
        max_index = len(palette)-1
        transform_value = (float(value-minval) / (maxval-minval)) * max_index
        int_value, float_value = divmod(transform_value, 1)
        int_value = int(int_value)

        # Nearest color pair and the difference
        g0 = palette[int_value]
        g1 = palette[min(int_value+1, max_index)]
        gd = g1-g0

        return g0+gd

    @staticmethod
    def colorize(value, minval, maxval, palette):
        """Convert value to color tag"""
        color = ColorTransformation.color_transformation(value, minval, maxval, palette)
        return '#' + '%02x' % color[0] + '%02x' % color[1] + '%02x' % color[2]
