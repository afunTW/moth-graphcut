"""
Predefined ttk style
"""
import logging
from tkinter import ttk

LOGGER = logging.getLogger(__name__)

class TTKStyle(ttk.Style):
    def __init__(self, style_name, **kwargs):
        super().__init__()
        self.configure(style_name, **kwargs)


if __name__ == '__main__':
    import tkinter

    root = tkinter.Tk()
    root.wm_title('DEMO - {}'.format(__file__))
    TTKStyle('H1.TLabel', font=('Helvetica',32))
    TTKStyle('H2.TLabel', font=('Helvetica',24))
    TTKStyle('H3.TLabel', font=('Helvetica',18))
    TTKStyle('H4.TLabel', font=('Helvetica',16))
    TTKStyle('H5.TLabel', font=('Helvetica',13))
    TTKStyle('H6.TLabel', font=('Helvetica',10))
    ttk.Label(root, text='H1 header - text size 32', style='H1.TLabel').grid(row=0, column=0, sticky='w')
    ttk.Label(root, text='H2 header - text size 24', style='H2.TLabel').grid(row=1, column=0, sticky='w')
    ttk.Label(root, text='H3 header - text size 18', style='H3.TLabel').grid(row=2, column=0, sticky='w')
    ttk.Label(root, text='H4 header - text size 16', style='H4.TLabel').grid(row=3, column=0, sticky='w')
    ttk.Label(root, text='H5 header - text size 13', style='H5.TLabel').grid(row=4, column=0, sticky='w')
    ttk.Label(root, text='H6 header - text size 10', style='H6.TLabel').grid(row=5, column=0, sticky='w')
    root.mainloop()
