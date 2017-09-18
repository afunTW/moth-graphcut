"""
Some support function for tkinter
"""
import logging
import tkinter

import numpy as np
from PIL import Image, ImageTk

LOGGER = logging.getLogger(__name__)

class TkConverter(object):
    def __init__(self):
        super().__init__()

    @staticmethod
    def read(image_path):
        img = Image.open(image_path)
        photo = ImageTk.PhotoImage(img)
        return photo

    @staticmethod
    def ndarray_to_photo(arr):
        h, w = arr.shape[0], arr.shape[1]
        byte_photo = Image.frombytes('L', (w, h), arr.astype('b').tostring())
        tk_photo = ImageTk.PhotoImage(byte_photo)
        return tk_photo
