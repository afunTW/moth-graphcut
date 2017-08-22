"""
Predefined font setting for tkinter
"""
import logging
from tkinter import font

LOGGER = logging.getLogger(__name__)

class TkFonts(object):
    def __init__(self):
        super().__init__()
        self.size = 12
        self.weight = 'regular'

    @property
    def font(self):
        return font.Font(size=self.size, weight=self.weight)

    def h1(self):
        self.size = 32
        self.weight = 'bold'
        return self.font

    def h2(self):
        self.size = 24
        self.weight = 'bold'
        return self.font

    def h3(self):
        self.size = 18.72
        self.weight = 'bold'
        return self.font

    def h4(self):
        self.size = 16
        self.weight = 'bold'
        return self.font

    def h5(self):
        self.size = 13.28
        self.weight = 'bold'
        return self.font

    def h6(self):
        self.size = 10.72
        self.weight = 'bold'
        return self.font
