"""
Predefined frame
"""
import logging
from tkinter import Frame, LabelFrame

LOGGER = logging.getLogger(__name__)

class TkFrame(Frame):
    def __init__(self, *args, **kwargs):
        if 'padx' not in kwargs:
            kwargs['padx'] = 10
        if 'pady' not in kwargs:
            kwargs['pady'] = 10
        super().__init__(*args, **kwargs)

class TkLabelFrame(LabelFrame):
    def __init__(self, *args, **kwargs):
        if 'padx' not in kwargs:
            kwargs['padx'] = 10
        if 'pady' not in kwargs:
            kwargs['pady'] = 10
        super().__init__(*args, **kwargs)
