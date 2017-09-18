"""
Predefined ttk style
"""
import logging
from tkinter import ttk

LOGGER = logging.getLogger(__name__)

class TTKStyle(ttk.Style):
    def __init__(self, style_name, **kwargs):
        super().__init__()
        self.theme_use('alt')
        self.configure(style_name, **kwargs)

def init_css():
    TTKStyle('H1.TLabel', font=('',32, 'bold'), background='white')
    TTKStyle('H2.TLabel', font=('',24, 'bold'), background='white')
    TTKStyle('H3.TLabel', font=('',18), background='white')
    TTKStyle('H4.TLabel', font=('',16), background='white')
    TTKStyle('H5.TLabel', font=('',13), background='white')
    TTKStyle('H6.TLabel', font=('',10), background='white')
    TTKStyle('H1.TCheckbutton', font=('',32), background='white')
    TTKStyle('H2.TCheckbutton', font=('',24), background='white')
    TTKStyle('H3.TCheckbutton', font=('',18), background='white')
    TTKStyle('H4.TCheckbutton', font=('',16), background='white')
    TTKStyle('H5.TCheckbutton', font=('',13), background='white')
    TTKStyle('H6.TCheckbutton', font=('',10), background='white')
    TTKStyle('White.Horizontal.TScale', background='white')

if __name__ == '__main__':
    import tkinter

    root = tkinter.Tk()
    root.wm_title('DEMO - {}'.format(__file__))
    init_css()
    ttk.Label(root, text='H1 header - text size 32', style='H1.TLabel').grid(row=0, column=0, sticky='w')
    ttk.Label(root, text='H2 header - text size 24', style='H2.TLabel').grid(row=1, column=0, sticky='w')
    ttk.Label(root, text='H3 header - text size 18', style='H3.TLabel').grid(row=2, column=0, sticky='w')
    ttk.Label(root, text='H4 header - text size 16', style='H4.TLabel').grid(row=3, column=0, sticky='w')
    ttk.Label(root, text='H5 header - text size 13', style='H5.TLabel').grid(row=4, column=0, sticky='w')
    ttk.Label(root, text='H6 header - text size 10', style='H6.TLabel').grid(row=5, column=0, sticky='w')
    root.mainloop()
