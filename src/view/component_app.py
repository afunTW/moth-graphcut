import logging
import os
import sys
import tkinter
from inspect import currentframe, getframeinfo
from tkinter import ttk
sys.path.append('../..')

from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.template import TkViewer
from src.view.tkframe import TkFrame
from src.view.ttkstyle import TTKStyle, init_css

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)
OUTFILE_TYPE = [('.npy', 'npy'), ('.dat', 'dat'), ('.txt', 'txt')]


class EntryThermalComponentViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._init_window(zoom=False)
        self._init_frame()
        self._init_style()

    # init tk frame and layout
    def _init_frame(self):
        # root
        self.frame_root = TkFrame(self.root)
        self.frame_root.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_root, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_root, 0)

        # body
        self.frame_body = TkFrame(self.frame_root)
        self.frame_body.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_body, 0, 1, 2, 3)
        self.set_all_grid_columnconfigure(self.frame_body, 0)

        # body > option
        self.frame_option = TkFrame(self.frame_body)
        self.frame_option.grid(row=0, column=0, sticky='w')
        self.set_all_grid_rowconfigure(self.frame_option, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_option, *[i for i in range(len(OUTFILE_TYPE)+1)])

        # body > upload
        self.frame_upload = TkFrame(self.frame_body)
        self.frame_upload.grid(row=1, column=0, sticky='w')
        self.set_all_grid_rowconfigure(self.frame_upload, 0, 1, 2, 3, 4)
        self.set_all_grid_columnconfigure(self.frame_upload, 0, 1, 2)

        # body > output
        self.frame_output = TkFrame(self.frame_body)
        self.frame_output.grid(row=2, column=0, sticky='w')
        self.set_all_grid_rowconfigure(self.frame_output, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_output, 0, 1)

        # footer
        self.frame_footer = TkFrame(self.frame_root)
        self.frame_footer.grid(row=1, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_footer, 0)
        self.set_all_grid_columnconfigure(self.frame_footer, 0, 1)

        # footer > state
        self.frame_state = TkFrame(self.frame_footer)
        self.frame_state.grid(row=0, column=0, sticky='w')
        self.set_all_grid_rowconfigure(self.frame_state, 0)
        self.set_all_grid_columnconfigure(self.frame_state, 0)

        # footer > btn
        self.frame_btn = TkFrame(self.frame_footer)
        self.frame_btn.grid(row=0, column=1, sticky='e')
        self.set_all_grid_rowconfigure(self.frame_btn, 0)
        self.set_all_grid_columnconfigure(self.frame_btn, 0)

        self._init_widget_body()
        self._init_widget_footer()

    # init ttk style
    def _init_style(self):
        init_css()
        TTKStyle('H5Bold.TLabel', font=('', 13, 'bold'))
        TTKStyle('Title.TLabel', font=('', 13, 'bold'))
        TTKStyle('H5.TLabel', font=('', 13))
        TTKStyle('H5.TButton', font=('', 13))
        TTKStyle('H5.TRadiobutton', font=('', 13))

    # init ttk body widget
    def _init_widget_body(self):
        # option: out filetype
        self.label_option = ttk.Label(self.frame_option, text=u'輸出檔案類型: ', style='Title.TLabel')
        self.label_option.grid(row=0, column=0, sticky='w')
        self.val_filetype = tkinter.StringVar()
        self.val_filetype.set('npy')
        self.radiobtn_filetype = []
        for i, filetype in enumerate(OUTFILE_TYPE):
            text, mode = filetype
            radiobtn = ttk.Radiobutton(self.frame_option, text=text, variable=self.val_filetype, value=mode, style='H5.TRadiobutton')
            radiobtn.grid(row=0, column=i+1, sticky='w', padx=10)
            self.radiobtn_filetype.append(radiobtn)

        # option: save visual img
        self.label_visual_option = ttk.Label(self.frame_option, text=u'輸出成果圖: ', style='Title.TLabel')
        self.label_visual_option.grid(row=1, column=0, sticky='w')
        self.val_visual = tkinter.StringVar()
        self.val_visual.set('n')
        self.radiobtn_visual = []
        for i, op in enumerate([(u'是', 'y'), (u'否', 'n')]):
            text, option = op
            radiobtn = ttk.Radiobutton(self.frame_option, text=text, variable=self.val_visual, value=option, style='H5.TRadiobutton')
            radiobtn.grid(row=1, column=i+1, sticky='w', padx=10)
            self.radiobtn_visual.append(radiobtn)

        # upload: thermal txt directory
        self.label_thermal = ttk.Label(self.frame_upload, text=u'溫度檔資料夾: ', style='Title.TLabel')
        self.label_thermal.grid(row=0, column=0, sticky='w')
        self.btn_thermal_txt_upload = ttk.Button(self.frame_upload, text=u'上傳', width=4, style='H5.TButton')
        self.btn_thermal_txt_upload.grid(row=0, column=1, sticky='w', padx=10)
        self.label_thermal_path = ttk.Label(self.frame_upload, text=u'N/A', style='H5.TLabel')
        self.label_thermal_path.grid(row=0, column=2, sticky='w')

        # upload: original image
        self.label_component = ttk.Label(self.frame_upload, text=u'部位原圖資料夾: ', style='Title.TLabel')
        self.label_component.grid(row=1, column=0, sticky='w')
        self.btn_component_upload = ttk.Button(self.frame_upload, text=u'上傳', width=4, style='H5.TButton')
        self.btn_component_upload.grid(row=1, column=1, sticky='w', padx=10)
        self.label_component_path = ttk.Label(self.frame_upload, text=u'N/A', style='H5.TLabel')
        self.label_component_path.grid(row=1, column=2, sticky='w')

        # upload: transform matrix
        self.label_transform_matrix = ttk.Label(self.frame_upload, text=u'轉換矩陣: ', style='Title.TLabel')
        self.label_transform_matrix.grid(row=2, column=0, sticky='w')
        self.btn_transform_matrix_upload = ttk.Button(self.frame_upload, text=u'上傳', width=4, style='H5.TButton')
        self.btn_transform_matrix_upload.grid(row=2, column=1, sticky='w', padx=10)
        self.label_transform_matrix_path = ttk.Label(self.frame_upload, text=u'N/A', style='H5.TLabel')
        self.label_transform_matrix_path.grid(row=2, column=2, sticky='w')

        # upload: contour
        self.label_contour_meta = ttk.Label(self.frame_upload, text=u'輪廓資訊: ', style='Title.TLabel')
        self.label_contour_meta.grid(row=3, column=0, sticky='w')
        self.btn_contour_meta_upload = ttk.Button(self.frame_upload, text=u'上傳', width=4, style='H5.TButton')
        self.btn_contour_meta_upload.grid(row=3, column=1, sticky='w', padx=10)
        self.label_contour_meta_path = ttk.Label(self.frame_upload, text=u'N/A', style='H5.TLabel')
        self.label_contour_meta_path.grid(row=3, column=2, sticky='w')

        # output: file path
        self.label_output = ttk.Label(self.frame_output, text=u'輸出檔案路徑: ', style='Title.TLabel')
        self.label_output.grid(row=0, column=0, sticky='w')
        self.label_output_path = ttk.Label(self.frame_output, text=u'N/A', style='H5.TLabel')
        self.label_output_path.grid(row=0, column=1, sticky='w', columnspan=2)

        # output: img path
        self.label_visual = ttk.Label(self.frame_output, text=u'輸出圖片路徑: ', style='Title.TLabel')
        self.label_visual.grid(row=1, column=0, sticky='w')
        self.label_visual_path = ttk.Label(self.frame_output, text=u'N/A', style='H5.TLabel')
        self.label_visual_path.grid(row=1, column=1, sticky='w')

    # init ttk footer widget
    def _init_widget_footer(self):
        # state
        self.label_convert_state = ttk.Label(self.frame_state, text=u'共 N/A 份檔案 - 準備中', style='H5Bold.TLabel')
        self.label_convert_state.grid(row=0, column=0, sticky='w')

        # button: preview
        self.btn_preview = ttk.Button(self.frame_btn, text=u'預覽', style='H5.TButton')
        self.btn_preview.grid(row=0, column=0, sticky='e')

        # button: convert btn
        self.btn_convert = ttk.Button(self.frame_btn, text=u'轉換', style='H5.TButton')
        self.btn_convert.grid(row=0, column=1, sticky='e')

class PreviewComponentViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._im_h, self._im_w = 239, 320
        self._init_window(zoom=False)
        self._init_frame()
        self._init_style()

    # init tk frame and layout
    def _init_frame(self):
        # root
        self.frame_root = TkFrame(self.root)
        self.frame_root.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_root, 0, 1, 2)
        self.set_all_grid_columnconfigure(self.frame_root, 0)

        # head
        self.frame_head = TkFrame(self.frame_root)
        self.frame_head.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_head, 0)
        self.set_all_grid_columnconfigure(self.frame_head, 0)

        # body
        self.frame_body = TkFrame(self.frame_root)
        self.frame_body.grid(row=1, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_body, 0)
        self.set_all_grid_columnconfigure(self.frame_body, 0, 1)

        # body > thermal
        self.frame_thermal = TkFrame(self.frame_body, bg='')
        self.frame_thermal.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_thermal, 0)
        self.set_all_grid_columnconfigure(self.frame_thermal, 0)

        # body > cut
        self.frame_cut = TkFrame(self.frame_body)
        self.frame_cut.grid(row=0, column=1, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_cut, 0)
        self.set_all_grid_columnconfigure(self.frame_cut, 0)

        # footer
        self.frame_footer = TkFrame(self.frame_root)
        self.frame_footer.grid(row=2, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_footer, 0)
        self.set_all_grid_columnconfigure(self.frame_footer, 0)

        self._init_widget_head()
        self._init_widget_body()
        self._init_widget_footer()

    # init ttk style
    def _init_style(self):
        init_css()
        TTKStyle('H2Gray.TLabel', font=('', 24, 'bold'), bg='gray56')

    # init ttk widget for frame head
    def _init_widget_head(self):
        # show frame info
        self.label_frameinfo = ttk.Label(
            self.frame_head,
            text=u'Image {}, Frame #{}'.format('N/A', 'N/A'),
            style='H2Gray.TLabel'
        )
        self.label_frameinfo.grid(row=0, column=0, sticky='w', padx=10)

    # init ttk widget for frame body
    def _init_widget_body(self):
        # thermal > original thermal image
        self.photo_original_thermal = ImageNP.generate_checkboard((self._im_h, self._im_w), 10)
        self.photo_original_thermal = TkConverter.ndarray_to_photo(self.photo_original_thermal)
        self.label_original_thermal = ttk.Label(self.frame_thermal, image=self.photo_original_thermal)
        self.label_original_thermal.grid(row=0, column=0, sticky='news')

        # cut > fl, fr, bl, br, body
        self.set_all_grid_rowconfigure(self.frame_cut, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_cut, 0, 1, 2)
        self.photo_small = ImageNP.generate_checkboard((self._im_h//2, self._im_w//3), 10)
        self.photo_small = TkConverter.ndarray_to_photo(self.photo_small)
        self.photo_large = ImageNP.generate_checkboard((self._im_h, self._im_w//3), 10)
        self.photo_large = TkConverter.ndarray_to_photo(self.photo_large)
        self.label_cut_fl = ttk.Label(self.frame_cut, image=self.photo_small)
        self.label_cut_fl.grid(row=0, column=0, sticky='news')
        self.label_cut_fr = ttk.Label(self.frame_cut, image=self.photo_small)
        self.label_cut_fr.grid(row=0, column=1, sticky='news')
        self.label_cut_bl = ttk.Label(self.frame_cut, image=self.photo_small)
        self.label_cut_bl.grid(row=1, column=0, sticky='news')
        self.label_cut_br = ttk.Label(self.frame_cut, image=self.photo_small)
        self.label_cut_br.grid(row=1, column=1, sticky='news')
        self.label_cut_body = ttk.Label(self.frame_cut, image=self.photo_large)
        self.label_cut_body.grid(row=0, column=2, sticky='news', rowspan=2)

    # init ttk widget for frame footer
    def _init_widget_footer(self):
        # replay
        self.btn_replay = ttk.Button(self.frame_footer, text=u'重播', style='H5.TButton')
        self.btn_replay.grid(row=0, column=0, sticky='e', padx=10)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    entry = EntryThermalComponentViewer()
    entry.mainloop()

