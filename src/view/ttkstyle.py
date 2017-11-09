"""
Predefined ttk style
"""
import os
import logging
from tkinter import ttk

LOGGER = logging.getLogger(__name__)

class TTKStyle(ttk.Style):
    def __init__(self, style_name, theme='default', **kwargs):
        super().__init__()
        self.theme_use(theme)
        self.configure(style_name, **kwargs)

def init_css():
    theme = 'default'
    if os.name == 'posix':
        theme = 'alt'
    TTKStyle('H1.TLabel', theme=theme, font=('',32, 'bold'), background='white')
    TTKStyle('H2.TLabel', theme=theme, font=('',24, 'bold'), background='white')
    TTKStyle('H3.TLabel', theme=theme, font=('',18), background='gray82')
    TTKStyle('H4.TLabel', theme=theme, font=('',16), background='gray82')
    TTKStyle('H5.TLabel', theme=theme, font=('',13), background='gray82')
    TTKStyle('H6.TLabel', theme=theme, font=('',10), background='gray82')
    TTKStyle('H1.TButton', theme=theme, font=('',32, 'bold'), background='white')
    TTKStyle('H2.TButton', theme=theme, font=('',24, 'bold'), background='white')
    TTKStyle('H3.TButton', theme=theme, font=('',18), background='gray82')
    TTKStyle('H4.TButton', theme=theme, font=('',16), background='gray82')
    TTKStyle('H5.TButton', theme=theme, font=('',13), background='gray82')
    TTKStyle('H6.TButton', theme=theme, font=('',10), background='gray82')
    TTKStyle('H1.TLabelframe', theme=theme, background='white')
    TTKStyle('H1.TLabelframe.Label', theme=theme, font=('', 32, 'bold'), background='white')
    TTKStyle('H2.TLabelframe', theme=theme, background='white')
    TTKStyle('H2.TLabelframe.Label', theme=theme, font=('', 24, 'bold'), background='white')
    TTKStyle('H3.TLabelframe', theme=theme, background='gray82')
    TTKStyle('H3.TLabelframe.Label', theme=theme, font=('', 18), background='gray82')
    TTKStyle('H4.TLabelframe', theme=theme, background='gray82')
    TTKStyle('H4.TLabelframe.Label', theme=theme, font=('', 16), background='gray82')
    TTKStyle('H5.TLabelframe', theme=theme, background='gray82')
    TTKStyle('H5.TLabelframe.Label', theme=theme, font=('', 13, 'bold'), background='gray82')
    TTKStyle('H6.TLabelframe', theme=theme, background='gray82')
    TTKStyle('H6.TLabelframe.Label', theme=theme, font=('', 10), background='gray82')
    TTKStyle('H1.TCheckbutton', theme=theme, font=('',32, 'bold'), background='gray82')
    TTKStyle('H2.TCheckbutton', theme=theme, font=('',24, 'bold'), background='gray82')
    TTKStyle('H3.TCheckbutton', theme=theme, font=('',18), background='gray82')
    TTKStyle('H4.TCheckbutton', theme=theme, font=('',16), background='gray82')
    TTKStyle('H5.TCheckbutton', theme=theme, font=('',13), background='gray82')
    TTKStyle('H6.TCheckbutton', theme=theme, font=('',10), background='gray82')
    TTKStyle('H1.TRadiobutton', theme=theme, font=('', 32, 'bold'), background='gray82')
    TTKStyle('H2.TRadiobutton', theme=theme, font=('', 24, 'bold'), background='gray82')
    TTKStyle('H3.TRadiobutton', theme=theme, font=('', 18), background='gray82')
    TTKStyle('H4.TRadiobutton', theme=theme, font=('', 16), background='gray82')
    TTKStyle('H5.TRadiobutton', theme=theme, font=('', 13), background='gray82')
    TTKStyle('H6.TRadiobutton', theme=theme, font=('', 10), background='gray82')
    TTKStyle('Gray.Horizontal.TScale', theme=theme, padding=20, background='gray82')

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
    ttk.Label(root, text='H1 checkbtn - text size 32', style='H1.TCheckbutton').grid(row=0, column=1, sticky='w')
    ttk.Label(root, text='H2 checkbtn - text size 24', style='H2.TCheckbutton').grid(row=1, column=1, sticky='w')
    ttk.Label(root, text='H3 checkbtn - text size 18', style='H3.TCheckbutton').grid(row=2, column=1, sticky='w')
    ttk.Label(root, text='H4 checkbtn - text size 16', style='H4.TCheckbutton').grid(row=3, column=1, sticky='w')
    ttk.Label(root, text='H5 checkbtn - text size 13', style='H5.TCheckbutton').grid(row=4, column=1, sticky='w')
    ttk.Label(root, text='H6 checkbtn - text size 10', style='H6.TCheckbutton').grid(row=5, column=1, sticky='w')
    root.mainloop()
