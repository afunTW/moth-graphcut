import cv2
import numpy as np
import logging

from . import grabcut
from scipy.ndimage.filters import gaussian_filter


class GrabcutProcess(object):
    '''
    ===============================================================================
    A wrapper to do grabcut for one picture
    ===============================================================================
    '''
    def __init__(self, filename, iter_times=1):
        self.filename = filename

        assert isinstance(iter_times, int) and iter_times > 0
        self.__parts = [grabcut.Grabcut(filename) for _ in range(iter_times)]
        self.__activated = False

        # non-interactive
        self.__rect = None
        self.__mask_records = None
        self.__segment_count = None

    @property
    def orig_image(self):
        return self.__parts[0].orig_image

    @property
    def parts(self):
        return self.__parts

    @property
    def activated(self):
        return self.__activated

    @property
    def rect(self):
        return [_.rect for _ in self.__parts]

    @rect.setter
    def rect(self, coor):
        assert isinstance(coor, list)
        for i, xy in enumerate(coor):
            assert self.__parts[i]
            self.__parts[i].rect = xy

    @property
    def mask_records(self):
        return self.__mask_records

    @mask_records.setter
    def mask_records(self, records):
        assert isinstance(records, list)
        for i, r in enumerate(records):
            assert self.__parts[i]
            self.__parts[i].mask_records = r

    @property
    def segment_count(self):
        return self.__segment_count

    @segment_count.setter
    def segment_count(self, counts):
        assert isinstance(counts, list)
        for i, c in enumerate(counts):
            assert self.__parts[i]
            self.__parts[i].segment_count = c

    def active(self):
        for i in self.__parts: i.active()
        self.__activated = True

    def simulate(self):
        for i in self.__parts: i.simulate()

    def image_or(self, *part_index):
        assert len(part_index) > 0
        output = np.zeros(self.orig_image.shape, dtype=np.uint8)

        for i, index in enumerate(part_index):
            assert isinstance(index, int) and self.__parts[index]
            output = np.bitwise_or(output, self.__parts[index].output)

        return output

    def blur_image_or(self, mask_color, sigma, *part_index):
        assert isinstance(sigma, int)
        output = self.image_or(*part_index)
        output = gaussian_filter(output, sigma)

        if mask_color:
            output = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
            output[np.where(output != 0)] = mask_color
            output = cv2.cvtColor(output, cv2.COLOR_GRAY2BGR)

        return output

    def remain_image(self, *part_index):
        assert len(part_index) > 0
        output = self.orig_image.copy()

        for i, index in enumerate(part_index):
            assert isinstance(index, int) and self.__parts[index]
            output = np.bitwise_xor(output, self.__parts[index].output)

        return output

    def track_image(self, *part_index):
        assert len(part_index) > 0
        output = self.orig_image.copy()

        for i, index in enumerate(part_index):
            assert isinstance(index, int) and self.__parts[index]

            # rect
            ix, iy, w, h = self.__parts[index].rect
            cv2.rectangle(output, (ix, iy), (ix+w, iy+h), [255, 0, 0], 2)

            # circle:
            for record in self.__parts[index].mask_records:
                cv2.circle(
                    output,
                    record['coordinate'],
                    record['thickness'],
                    record['value']['color'],
                    -1)
                cv2.circle(
                    output,
                    record['coordinate'],
                    record['thickness'],
                    record['value']['val'],
                    -1)

        return output
