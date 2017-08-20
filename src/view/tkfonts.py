"""
Predefined font setting for tkinter
"""
import logging
from tkinter import font

LOGGER = logging.getLogger(__name__)

class TkFonts(object):
    def __init__(self):
        super().__init__()

    def h1(self, text=''):
        self.text = text
        self.size = 32
        return font.Font(size=32)
