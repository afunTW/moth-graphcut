import logging
import os
import sys
import tkinter
from tkinter import ttk
sys.path.append('../..')

import cv2
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.template import TkViewer
from src.view.tkfonts import TkFonts
from src.view.tkframe import TkFrame, TkLabelFrame
from src.view.ttkstyle import TTKStyle, init_css

LOGGER = logging.getLogger(__name__)

THRESHOLD_OPTION = [(u'手動', 'manual'), ('Mean Adaptive', 'mean'), ('Gaussian Adaptive', 'gaussian')]

class GraphCutViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._im_w, self._im_h = 800, 533
        self._init_window(zoom=False)
        self._init_style()
        self._init_frame()

    def _init_style(self):
        init_css()
        TTKStyle('H4Padding.TLabelframe', background='gray82')
        TTKStyle('H4Padding.TLabelframe.Label',  font=('', 16), background='gray82')
        TTKStyle('H2BlackdBold.TLabel', font=('', 24, 'bold'), background='white', foreground='black')
        TTKStyle('H2RedBold.TLabel', font=('', 24, 'bold'), background='white', foreground='red')
        self.font = TkFonts()

    # init frame
    def _init_frame(self):
        # root
        self.frame_root = TkFrame(self.root, bg='white')
        self.frame_root.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_root, 0, 1, 2)
        self.set_all_grid_columnconfigure(self.frame_root, 0)

        # head
        self.frame_head = TkFrame(self.frame_root, bg='white')
        self.frame_head.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_head, 0)
        self.set_all_grid_columnconfigure(self.frame_head, 0)

        # body
        self.frame_body = TkFrame(self.frame_root, bg='black')
        self.frame_body.grid(row=1, column=0, sticky='news')
        self.set_all_grid_columnconfigure(self.frame_body, 0, 1)
        self.set_all_grid_rowconfigure(self.frame_body, 0)

        # body > panel
        self.frame_panel = TkFrame(self.frame_body, bg='light pink')
        self.frame_panel.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_panel, 0)
        self.set_all_grid_columnconfigure(self.frame_panel, 0)

        # body > display
        self.frame_display = TkFrame(self.frame_body, bg='royal blue')
        self.frame_display.grid(row=0, column=1, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_display, 0)
        self.set_all_grid_columnconfigure(self.frame_display, 0)

        # footer
        self.frame_footer = TkFrame(self.frame_root, bg='gray82')
        self.frame_footer.grid(row=2, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_footer, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_footer, 0)

        # footer > panel setting
        self.frame_panel_setting = ttk.LabelFrame(self.frame_footer, text=u'輸入圖片選項: ', style='H4Padding.TLabelframe')
        self.frame_panel_setting.grid(row=0, column=0, sticky='news', pady=10)
        self.set_all_grid_rowconfigure(self.frame_panel_setting, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_panel_setting, 0)

        # footer > panel setting > template option
        self.frame_template_options = TkFrame(self.frame_panel_setting, bg='gray82', pady=5)
        self.frame_template_options.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_template_options, 0)
        self.set_all_grid_columnconfigure(self.frame_template_options, 0)

        # footer > panel setting > gamma
        self.frame_gamma = TkFrame(self.frame_panel_setting, bg='gray82', pady=5)
        self.frame_gamma.grid(row=1, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_gamma, 0)
        self.set_all_grid_columnconfigure(self.frame_gamma, 0)

        # footer > display setting
        self.frame_display_setting = ttk.LabelFrame(self.frame_footer, text=u'輸出圖片選項: ', style='H4Padding.TLabelframe')
        self.frame_display_setting.grid(row=1, column=0, sticky='news', pady=10)
        self.set_all_grid_rowconfigure(self.frame_display_setting, 0)
        self.set_all_grid_columnconfigure(self.frame_display_setting, 0)

        # footer > display setting > threshold options
        self.frame_threshold_options = TkFrame(self.frame_display_setting, bg='gray82', pady=5)
        self.frame_threshold_options.grid(row=0, column=0, sticky='news')

        # footer > display setting > manual threshold
        self.frame_manual_threshold = TkFrame(self.frame_display_setting, bg='gray82', pady=5)
        self.frame_manual_threshold.grid(row=1, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_manual_threshold, 0)
        self.set_all_grid_columnconfigure(self.frame_manual_threshold, 0)

        self._init_widget_head()
        self._init_widget_body()
        self._init_widget_footer()

    # init head widget
    def _init_widget_head(self):
        self.set_all_grid_rowconfigure(self.frame_head, 0, 1)
        self.label_state = ttk.Label(self.frame_head, text=u'現在模式: N/A', style='H2.TLabel')
        self.label_state.grid(row=0, column=0, sticky='w')
        self.label_resize = ttk.Label(self.frame_head, text=u'原有尺寸 N/A-> 顯示尺寸 N/A', style='H2.TLabel')
        self.label_resize.grid(row=1, column=0, sticky='w')

    # init body widget
    def _init_widget_body(self):
        # panel
        self.label_panel = ttk.Label(self.frame_panel, text='Input Panel', style='H2.TLabel')
        self.label_panel.grid(row=0, column=0, sticky='ns')
        self.photo_panel = ImageNP.generate_checkboard((self._im_h, self._im_w), block_size=10)
        self.photo_panel = TkConverter.ndarray_to_photo(self.photo_panel)
        self.label_panel_image = ttk.Label(self.frame_panel, image=self.photo_panel)
        self.label_panel_image.grid(row=1, column=0, sticky='ns')

        # display
        self.label_display = ttk.Label(self.frame_display, text='Display', style='H2.TLabel')
        self.label_display.grid(row=0, column=0, sticky='ns')
        self.photo_display = self.photo_panel
        self.label_display_image = ttk.Label(self.frame_display, image=self.photo_display)
        self.label_display_image.grid(row=1, column=0, sticky='ns')

    # init footer widget
    def _init_widget_footer(self):
        # input panel template option
        self.label_template = ttk.Label(self.frame_template_options, text=u'過濾樣式: ', style='H5.TLabel')
        self.label_template.grid(row=0, column=0, sticky='w')

        # input panel gamma
        self.label_gamma = ttk.Label(self.frame_gamma, text=u'調整對比 ({:.2f}): '.format(1.), style='H5.TLabel')
        self.label_gamma.grid(row=0, column=0, sticky='w')
        self.val_scale_gamma = tkinter.DoubleVar()
        self.val_scale_gamma.set(1.0)
        self.scale_gamma = ttk.Scale(self.frame_gamma,
                                     orient=tkinter.HORIZONTAL,
                                     length=self._im_w*2,
                                     from_=0, to=25,
                                     variable=self.val_scale_gamma,
                                     style='Gray.Horizontal.TScale')
        self.scale_gamma.state(('active', '!disabled'))
        self.scale_gamma.grid(row=0, column=1, sticky='w')

        # display threshold option
        self.label_threshold_options = ttk.Label(self.frame_threshold_options, text=u'門檻值選項: ', style='H5.TLabel')
        self.label_threshold_options.grid(row=0, column=0, sticky='w')
        self.val_threshold_option = tkinter.StringVar()
        self.val_threshold_option.set(THRESHOLD_OPTION[0][-1])
        self.radiobtn_threshold_options = []
        for i, op in enumerate(THRESHOLD_OPTION):
            text, val = op
            radiobtn = ttk.Radiobutton(self.frame_threshold_options,
                                       text=text,
                                       variable=self.val_threshold_option,
                                       value=val,
                                       style='H5.TRadiobutton')
            radiobtn.grid(row=0, column=i+1, sticky='w', padx=10)
            self.radiobtn_threshold_options.append(radiobtn)

        # display threshold manual scale
        self.label_manual_threshold = ttk.Label(self.frame_manual_threshold, text=u'門檻值 ({:.2f}): '.format(250), style='H5.TLabel')
        self.label_manual_threshold.grid(row=0, column=0, sticky='w')
        self.val_manual_threshold = tkinter.DoubleVar()
        self.val_manual_threshold.set(250)
        self.scale_manual_threshold = ttk.Scale(self.frame_manual_threshold,
                                                orient=tkinter.HORIZONTAL,
                                                length=self._im_w*2,
                                                from_=1, to=254,
                                                variable=self.val_manual_threshold,
                                                style='Gray.Horizontal.TScale')
        self.scale_manual_threshold.state(('active', '!disabled'))
        self.scale_manual_threshold.grid(row=0, column=1, sticky='news', columnspan=len(THRESHOLD_OPTION))


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    graphcut_viewer = GraphCutViewer()
    graphcut_viewer.mainloop()
