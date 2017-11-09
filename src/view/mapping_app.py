"""
For mapping application
 - AutoMapping
 - ManualMapping
 - MappingResult
"""

import logging
import os
import sys
import tkinter
from inspect import currentframe, getframeinfo
from tkinter import ttk

sys.path.append('../..')
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.template import ImageViewer, TkViewer
from src.view.tkframe import TkFrame
from src.view.ttkstyle import TTKStyle, init_css

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)

# the entry to auto mapping
class EntryMappingViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._init_window(zoom=False)
        self._init_frame()
        self._init_style()
        self._init_widget()

    # init tk frame and layout
    def _init_frame(self):
        """root"""
        self.frame_root = TkFrame(self.root)
        self.frame_root.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_root, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_root, 0)

        """body"""
        self.frame_body = TkFrame(self.frame_root)
        self.frame_body.grid(row=0, column=0, sticky='w')
        self.set_all_grid_rowconfigure(self.frame_body, 0, 1)
        self.set_all_grid_columnconfigure(self.frame_body, 0, 1)

        """footer"""
        self.frame_footer = TkFrame(self.frame_root)
        self.frame_footer.grid(row=1, column=0, sticky='e')
        self.set_all_grid_rowconfigure(self.frame_footer, 0)
        self.set_all_grid_columnconfigure(self.frame_footer, 0, 1, 2)

    # init ttk style
    def _init_style(self):
        init_css()
        theme = 'default'
        if os.name == 'posix':
            theme = 'alt'
        TTKStyle('H5Bold.TLabel', theme=theme, font=('', 13))

    # init ttk widget
    def _init_widget(self):
        """body"""
        self.label_img = ttk.Label(self.frame_body, text=u'圖片路徑: ', style='H5Bold.TLabel')
        self.label_img.grid(row=0, column=0, sticky='w')
        self.label_img_path = ttk.Label(self.frame_body, text=u'N/A', style='H5.TLabel')
        self.label_img_path.grid(row=0, column=1, sticky='w')
        self.label_temp = ttk.Label(self.frame_body, text=u'熱像儀資料夾路徑: ', style='H5Bold.TLabel')
        self.label_temp.grid(row=1, column=0, sticky='w')
        self.label_temp_path = ttk.Label(self.frame_body, text=u'N/A', style='H5.TLabel')
        self.label_temp_path.grid(row=1, column=1, sticky='w')

        """footer"""
        self.btn_img_path = ttk.Button(self.frame_footer, text=u'載入圖片', style='H5.TButton')
        self.btn_img_path.grid(row=0, column=0, sticky='e')
        self.btn_temp_path = ttk.Button(self.frame_footer, text=u'選擇熱像儀資料夾', style='H5.TButton')
        self.btn_temp_path.grid(row=0, column=1, sticky='e')
        self.btn_ok = ttk.Button(self.frame_footer, text=u'確認', style='H5.TButton')
        self.btn_ok.grid(row=0, column=2, sticky='e')

# the interface to auto mapping
class AutoMappingViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._im_h, self._im_w = 239, 320

        self._init_window(zoom=False)
        self._init_style()
        theme = 'default'
        if os.name == 'posix':
            theme = 'alt'
        TTKStyle('H5.TButton', theme=theme, font=('', 13), background='white')
        self._init_frame()
        self._init_widget()

    # init tk frame and grid layout
    def _init_frame(self):
        # root
        self.frame_root = TkFrame(self.root, bg='white')
        self.frame_root.grid(row=0, column=0)
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
        self.set_all_grid_rowconfigure(self.frame_body, 0)
        self.set_all_grid_columnconfigure(self.frame_body, 0)

        # footer
        self.frame_footer = TkFrame(self.frame_root, bg='khaki1')
        self.frame_footer.grid(row=2, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_footer, 0)
        self.set_all_grid_columnconfigure(self.frame_footer, 0)

    def _init_widget(self):
        # head: message
        self.label_head_msg = ttk.Label(self.frame_head, text=u'自動修正結果: 原圖-修正後溫度圖=結果圖', style='H1.TLabel')
        self.label_head_msg.grid(row=0, column=0, sticky='news')

        # body reconfig
        self.set_all_grid_columnconfigure(self.frame_body, 0, 1, 2, 3, 4,)

        # body: original
        self.photo_original = ImageNP.generate_checkboard((self._im_h, self._im_w), block_size=10)
        self.photo_original = TkConverter.ndarray_to_photo(self.photo_original)
        self.label_original = ttk.Label(self.frame_body, image=self.photo_original)
        self.label_original.grid(row=0, column=0, sticky='news')

        # body: -
        self.label_minus = ttk.Label(self.frame_body, text=u' - ', style='H1.TLabel')
        self.label_minus.grid(row=0, column=1, sticky='news', padx=10)

        # body: warp thermal
        self.photo_warp_thermal = ImageNP.generate_checkboard((self._im_h, self._im_w), block_size=10)
        self.photo_warp_thermal = TkConverter.ndarray_to_photo(self.photo_warp_thermal)
        self.label_warp_thermal = ttk.Label(self.frame_body, image=self.photo_warp_thermal)
        self.label_warp_thermal.grid(row=0, column=2, sticky='news')

        # body: =
        self.label_equal = ttk.Label(self.frame_body, text=u' = ', style='H1.TLabel')
        self.label_equal.grid(row=0, column=3, sticky='news', padx=10)

        # body: result
        self.photo_mapping_result = ImageNP.generate_checkboard((self._im_h, self._im_w), block_size=10)
        self.photo_mapping_result = TkConverter.ndarray_to_photo(self.photo_mapping_result)
        self.label_mapping_result = ttk.Label(self.frame_body, image=self.photo_mapping_result)
        self.label_mapping_result.grid(row=0, column=4, sticky='news')

        # footer reconfig

        # footer
        self.button_reload = ttk.Button(self.frame_footer, text=u'重新載入', style='H5.TButton')
        self.button_reload.grid(row=0, column=0, sticky='e')
        self.button_manual = ttk.Button(self.frame_footer, text=u'手動定位', style='H5.TButton')
        self.button_manual.grid(row=0, column=1, sticky='e')
        self.button_ok = ttk.Button(self.frame_footer, text=u'確認', style='H5.TButton')
        self.button_ok.grid(row=0, column=2, sticky='e')

# the interface to manual mapping
class ManualMappingViewer(TkViewer):
    def __init__(self):
        super().__init__()
        self._img_h, self._img_w = 239, 320
        self._init_window(zoom=False)
        self._init_style()
        theme = 'default'
        if os.name == 'posix':
            theme = 'alt'
        TTKStyle('H5.TButton', theme=theme, font=('', 13), background='white')
        self._init_frame()
        self._init_widget_head()
        self._init_widget_body()
        self._init_widget_footer()

    # init tk frame and grid layout
    def _init_frame(self):
        """root"""
        self.frame_root = TkFrame(self.root, bg='white')
        self.frame_root.grid(row=0, column=0)
        self.set_all_grid_columnconfigure(self.frame_root, 0)
        self.set_all_grid_rowconfigure(self.frame_root, 0, 1, 2)

        """root.header"""
        self.frame_nav = TkFrame(self.frame_root, bg='white')
        self.frame_nav.grid(row=0, column=0, sticky='news')
        self.set_all_grid_columnconfigure(self.frame_nav, 0)
        self.set_all_grid_rowconfigure(self.frame_nav, 0, 1)

        """root.body"""
        self.frame_body = TkFrame(self.frame_root, bg='black')
        self.frame_body.grid(row=1, column=0, sticky='news')
        self.set_all_grid_columnconfigure(self.frame_body, 0, 1)
        self.set_all_grid_rowconfigure(self.frame_body, 0)

        """root.body.frame_panel"""
        self.frame_panel = TkFrame(self.frame_body, bg='light pink')
        self.frame_panel.grid(row=0, column=0, sticky='news')
        self.set_all_grid_columnconfigure(self.frame_panel, 0)
        self.set_all_grid_rowconfigure(self.frame_panel, 0, 1)

        """root.body.frame_display"""
        self.frame_display = TkFrame(self.frame_body, bg='royal blue')
        self.frame_display.grid(row=0, column=1, sticky='news')
        self.set_all_grid_columnconfigure(self.frame_display, 0)
        self.set_all_grid_rowconfigure(self.frame_display, 0, 1)

        """root.footer"""
        self.frame_footer = TkFrame(self.frame_root)
        self.frame_footer.grid(row=2, column=0, sticky='news')
        self.set_all_grid_columnconfigure(self.frame_footer, 0)
        self.set_all_grid_rowconfigure(self.frame_footer, 0)

    # init head widget
    def _init_widget_head(self):

        self.label_panel_state = ttk.Label(
            self.frame_nav, text=u'Original - 尚餘 {} 個標記'.format(4), style='H2.TLabel'
        )
        self.label_display_state = ttk.Label(
            self.frame_nav, text=u'Thermal - 尚餘 {} 個標記'.format(4), style='H2.TLabel'
        )
        self.label_panel_state.grid(row=0, column=0, sticky='w')
        self.label_display_state.grid(row=1, column=0, sticky='w')

    # init body widget
    def _init_widget_body(self):
        """Panel/Display label"""
        self.label_panel = ttk.Label(self.frame_panel, text='Original', style='H2.TLabel')
        self.label_display = ttk.Label(self.frame_display, text='Thermal', style='H2.TLabel')
        self.label_panel.grid(row=0, column=0)
        self.label_display.grid(row=0, column=0)

        """Panel/Display image"""
        # default output
        self.photo_panel = ImageNP.generate_checkboard((239, 320), block_size=10)
        self.photo_panel = TkConverter.ndarray_to_photo(self.photo_panel)
        self.photo_display = self.photo_panel

        self.label_panel_image = ttk.Label(self.frame_panel, image=self.photo_panel)
        self.label_panel_image.image = self.photo_panel
        self.label_panel_image.grid(row=2, column=0)
        self.label_display_image = ttk.Label(self.frame_display, image=self.photo_display)
        self.label_display_image.grid(row=2, column=0)

    # init footer widget
    def _init_widget_footer(self):
        self.button_reload = ttk.Button(self.frame_footer, text=u'自動標記', style='H5.TButton')
        self.button_reload.grid(row=0, column=0, sticky='e')
        self.button_preview = ttk.Button(self.frame_footer, text=u'預覽', style='H5.TButton')
        self.button_ok = ttk.Button(self.frame_footer, text=u'確認', style='H5.TButton')
        self.button_preview.grid(row=0, column=1, sticky='e')
        self.button_ok.grid(row=0, column=2, sticky='e')

# the interface to preview
class PreviewViewer(TkViewer):
    def __init__(self, img, parent=None):
        self._preview_img = img
        self._init_window(zoom=False, parent=parent)
        self._init_style()
        self._init_frame()

    def _init_frame(self):
        self.frame_root = TkFrame(self.root)
        self.frame_root.grid(row=0, column=0, sticky='news')
        self.set_all_grid_rowconfigure(self.frame_root, 0)
        self.set_all_grid_columnconfigure(self.frame_root, 0)
        self._init_widget()

    def _init_widget(self):
        self._preivew_photo = TkConverter.cv2_to_photo(self._preview_img)
        self.label_preview = ttk.Label(self.frame_root, image=self._preivew_photo)
        self.label_preview.grid(row=0, column=0, sticky='news')

if __name__ == '__main__':
    """testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    # entry_viewer = EntryMappingViewer()
    # entry_viewer.mainloop()

    # automapping_viewer = AutoMappingViewer()
    # automapping_viewer.mainloop()

    manualmapping_viewer = ManualMappingViewer()
    manualmapping_viewer.mainloop()
