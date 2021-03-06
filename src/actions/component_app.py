import json
import logging
import os
import sys
import tkinter
from inspect import currentframe, getframeinfo
from tkinter.filedialog import askdirectory, askopenfilename
sys.path.append('../..')

import numpy as np
from PIL.ImageTk import PhotoImage

import cv2
from src.image.colormap import ColorMap
from src.image.imnp import ImageNP
from src.support.msg_box import MessageBox
from src.support.tkconvert import TkConverter
from src.view.component_app import (EntryThermalComponentViewer,
                                    PreviewComponentViewer)

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)

class EntryThermalComponentAction(EntryThermalComponentViewer):
    def __init__(self):
        super().__init__()
        # path
        self._thermal_dir_path = None
        self._component_dir_path = None
        self._transform_matrix_path = None
        self._contour_path = None
        self._output_dir_path = None
        self._output_visual_path = None

        # file
        self._component_img = None
        self._transform_matrix = None
        self._contour_meta = None

        self.btn_thermal_txt_upload.config(command=self._load_thermal_dir)
        self.btn_component_upload.config(command=self._load_component_img)
        self.btn_transform_matrix_upload.config(command=self._load_transform_matrix)
        self.btn_contour_meta_upload.config(command=self._load_contour_meta)
        self.btn_preview.config(command=self._preview)
        self.btn_convert.config(command=self._convert)
        self._sync_generate_save_path()
        self._sync_generate_visual_path()

    # load thermal directory
    def _load_thermal_dir(self):
        self._thermal_dir_path = askdirectory(
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
            title=u'選擇溫度檔資料夾 (.txt)'
        )

        if self._thermal_dir_path:
            LOGGER.info('Thermal txt directory - {}'.format(self._thermal_dir_path))
            frame_count = len(os.listdir(self._thermal_dir_path))
            self.label_thermal_path.config(text=self._thermal_dir_path)
            self.label_convert_state.config(text=u'共 {} 份檔案 - 準備中'.format(frame_count))

    # load original image path
    def _load_component_img(self):
        self._component_dir_path = askdirectory(
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
            title=u'選擇部位原圖資料夾'
        )

        if self._component_dir_path:
            LOGGER.info('Original image file - {}'.format(self._component_dir_path))
            filename = self._component_dir_path.split(os.sep)[-1].split('.')[0]
            self.label_component_path.config(text=self._component_dir_path)
            try:
                self._component_img = {
                    'foreleft': cv2.imread(os.path.join(self._component_dir_path, 'fore_left.png')),
                    'foreright': cv2.imread(os.path.join(self._component_dir_path, 'fore_right.png')),
                    'backleft': cv2.imread(os.path.join(self._component_dir_path, 'back_left.png')),
                    'backright': cv2.imread(os.path.join(self._component_dir_path, 'back_right.png')),
                    'body': cv2.imread(os.path.join(self._component_dir_path, 'body.png'))
                }
            except Exception as e:
                LOGGER.exception(e)
                Mbox = MessageBox()
                Mbox.alert(string=u'無法正確開啟原圖')

            # try to generate transform matrix path
            if self._transform_matrix_path is None or not self._transform_matrix_path:
                self._transform_matrix_path = os.path.join(self._component_dir_path.split('.')[0], 'transform_matrix.dat')
                if os.path.exists(self._transform_matrix_path):
                    LOGGER.info('Transform matrix file - {}'.format(self._transform_matrix_path))
                    self.label_transform_matrix_path.config(text=self._transform_matrix_path)
                    self._transform_matrix = np.fromfile(self._transform_matrix_path)
                    self._transform_matrix = self._transform_matrix.reshape(3, 3)
                else:
                    LOGGER.warning('Transform matrix file {} does not exist'.format(self._transform_matrix_path))

            # try to generate other necessary data path
            if self._contour_path is None or not self._contour_path:
                self._contour_path = os.path.join(self._component_dir_path.split('.')[0], 'metadata.json')
                if os.path.exists(self._contour_path):
                    self.label_contour_meta_path.config(text=self._contour_path)
                    LOGGER.info('Contour meta - {}'.format(self._contour_path))
                    with open(self._contour_path, 'r') as f:
                        self._contour_meta = json.load(f)
                else:
                    LOGGER.warning('Contour meta {} does not exist'.foramt(self._contour_path))

    # load transform matrix path
    def _load_transform_matrix(self):
        self._transform_matrix_path = askopenfilename(
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
            title=u'選擇轉換矩陣路徑',
            filetypes=(('Numpy array', '*.dat'),)
        )

        if self._transform_matrix_path:
            LOGGER.info('Transform matrix file - {}'.format(self._transform_matrix_path))
            self.label_transform_matrix_path.config(text=self._transform_matrix_path)
            self._transform_matrix = np.fromfile(self._transform_matrix_path)
            self._transform_matrix = self._transform_matrix.reshape(3, 3)

    # load contour metadata path
    def _load_contour_meta(self):
        self._contour_path = askopenfilename(
            initialdir=os.path.abspath(os.path.join(__FILE__, '../../../')),
            title=u'選擇輪廓資訊路徑',
            filetypes=(('JSON file', '*.json'),)
        )

        if self._contour_path:
            LOGGER.info('Contour meta - {}'.format(self._contour_path))
            self.label_contour_meta_path.config(text=self._contour_path)
            with open(self._contour_path, 'r') as f:
                self._contour_meta = json.load(f)

    # sync save path
    def _sync_generate_save_path(self):
        if self._thermal_dir_path and self.val_filetype.get():
            self._output_dir_path = '{}_warp_{}'.format(self._thermal_dir_path, self.val_filetype.get())
            self.label_output_path.config(text=self._output_dir_path)

        self.label_output_path.after(10, self._sync_generate_save_path)

    # sync visual path
    def _sync_generate_visual_path(self):
        if self._thermal_dir_path and self.val_visual.get() == 'y':
            self._output_visual_path = '{}_component'.format(self._thermal_dir_path)
            self.label_visual_path.config(text=self._output_visual_path)
        else:
            self._output_visual_path = None
            self.label_visual_path.config(text='N/A')

        self.label_visual_path.after(10, self._sync_generate_visual_path)

    # check if all necessary data is prepared
    def _check_data(self):
        if self._thermal_dir_path is None or not self._thermal_dir_path:
            LOGGER.warning('Please choose the thermal text data directory')
            Mbox = MessageBox()
            Mbox.alert(string=u'請選擇溫度圖檔案的資料夾')
            return False
        elif (
            self._component_img is None or
            self._component_img['foreleft'] is None or
            self._component_img['foreright'] is None or
            self._component_img['backleft'] is None or
            self._component_img['backright'] is None or
            self._component_img['body'] is None
        ):
            LOGGER.warning('Please provide the proper component image directory')
            Mbox = MessageBox()
            Mbox.alert(string=u'請上傳適當的圖檔')
            return False
        elif self._transform_matrix is None:
            LOGGER.warning('Please provide the proper transforma matrix file')
            Mbox = MessageBox()
            Mbox.alert(string=u'請上傳適當的轉換矩陣檔案')
            return False
        elif (
            self._contour_meta is None or
            sorted(set(self._contour_meta.keys())) != sorted(['fl', 'fr', 'bl', 'br', 'body', 'image']) or
            'cnts' not in self._contour_meta['fl'] or
            'cnts' not in self._contour_meta['fr'] or
            'cnts' not in self._contour_meta['bl'] or
            'cnts' not in self._contour_meta['br'] or
            'cnts' not in self._contour_meta['body']
        ):
            LOGGER.warning('Please provide the proper contour metadata')
            Mbox = MessageBox()
            Mbox.alert(string=u'請上傳適當的輪廓資料')
            return False
        elif self._output_dir_path is None:
            Mbox = MessageBox()
            Mbox.alert(string=u'無存檔路徑')
            LOGGER.error('No output path')
            return False
        else:
            return True

    # preview
    def _preview(self):
        component_key = ['foreleft', 'foreright', 'backleft', 'backright', 'body']
        if self._thermal_dir_path:
            # check thermal frame path
            thermal_frames = os.listdir(self._thermal_dir_path)
            thermal_frames = sorted(thermal_frames, key=lambda x: int(x.split('.')[0].split('_')[-1]))
            thermal_frames = [os.path.join(self._thermal_dir_path, i) for i in thermal_frames]

            # check component path
            gen_path = lambda x: os.path.join('{}_component'.format(self._thermal_dir_path), x)
            component_path = {part: gen_path(part) for part in component_key}
            for part, path in component_path.items():
                if not os.path.exists(path):
                    LOGGER.warning('No proper path for {}'.format(part))
                    Mbox = MessageBox()
                    Mbox.alert(string=u'沒有可預覽的圖片路徑')
                    return

            # operate per frame
            previewer = PreviewComponentAction(self.root)
            for i, frame_path in enumerate(thermal_frames):
                # thermal image preprocess
                frame_id = frame_path.split(os.sep)[-1].split('.')[0]

                # component image preprocess
                component_img = {}
                for part, path in component_path.items():
                    path = os.path.join(path, frame_id) + '.png'
                    component_img[part] = cv2.imread(path)
                    component_img[part] = TkConverter.cv2_to_photo(component_img[part])

                # update previewer
                previewer.label_frameinfo.config(text=u'Frame #{}'.format(i+1))
                previewer.update(
                    fl=component_img['foreleft'],
                    fr=component_img['foreright'],
                    bl=component_img['backleft'],
                    br=component_img['backright'],
                    body=component_img['body']
                )
                previewer.root.update()
            previewer.mainloop()


    # convert
    def _convert(self):
        if self._check_data():
            is_output_visual = True if self.val_visual.get() == 'y' else False
            output_file_format = self.val_filetype.get()
            thermal_frames = [os.path.join(self._thermal_dir_path, f) for f in os.listdir(self._thermal_dir_path)]
            thermal_frames = sorted(thermal_frames, key=lambda x: int(x.split(os.sep)[-1].split('.')[0].split('_')[-1]))
            component_cnts = {
                'foreleft': self._contour_meta['fl']['cnts'],
                'foreright': self._contour_meta['fr']['cnts'],
                'backleft': self._contour_meta['bl']['cnts'],
                'backright': self._contour_meta['br']['cnts'],
                'body': self._contour_meta['body']['cnts']
            }

            # view state
            self.label_convert_state.config(text=u'共 {} 份檔案 - 準備中'.format(len(thermal_frames)))
            self.root.update()

            # original image resize > threshold > get mask
            _ = np.loadtxt(open(thermal_frames[0], 'rb'), delimiter=',', skiprows=1)
            component_mask = {}
            for part, img in self._component_img.items():
                img = cv2.resize(img, _.shape[:2][::-1])
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                ret, mask = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY)
                component_mask[part] = mask

            # process each frame
            for idx, frame in enumerate(thermal_frames):
                frame_data = np.loadtxt(open(frame, 'rb'), delimiter=',', skiprows=1)
                thermal_map = ColorMap(frame_data)
                thermal_img = thermal_map.transform_to_rgb()

                # process each component
                for part, cnt in component_cnts.items():

                    # save visual path
                    if is_output_visual:
                        warp_thermal = cv2.warpPerspective(thermal_img, self._transform_matrix, thermal_img.shape[:2][::-1])
                        warp_thermal = warp_thermal.astype('float32')
                        warp_thermal = cv2.cvtColor(warp_thermal, cv2.COLOR_RGB2BGR)
                        warp_thermal[np.where(component_mask[part] == 0)] = 0
                        savedir = os.path.join(self._output_visual_path, part)
                        if not os.path.exists(savedir):
                            os.makedirs(savedir)
                        saveframe = os.path.join(savedir, frame.split(os.sep)[-1].split('.')[0])
                        savefile = saveframe + '.png'
                        cv2.imwrite(savefile, warp_thermal)
                        LOGGER.info('Save - {}'.format(savefile))

                    # save path
                    savedir = os.path.join(self._output_dir_path, part)
                    if not os.path.exists(savedir):
                        os.makedirs(savedir)

                    # warp thermal frame > mask
                    warp_component = cv2.warpPerspective(frame_data, self._transform_matrix, frame_data.shape[:2][::-1])
                    warp_component[np.where(component_mask[part] == 0)] = 0

                    # save
                    saveframe = os.path.join(savedir, frame.split(os.sep)[-1].split('.')[0])
                    savefile = None
                    if output_file_format == 'npy':
                        savefile = saveframe + '.npy'
                        np.save(savefile, warp_component)
                    elif output_file_format == 'dat':
                        savefile = saveframe + '.dat'
                        warp_component.tofile(savefile)
                    elif output_file_format == 'txt':
                        savefile = saveframe + '.txt'
                        np.savetxt(savefile, warp_component)
                    LOGGER.info('Save - {}'.format(savefile))

                self.label_convert_state.config(
                    text=u'{}/{} 份檔案 - 轉換中'.format(idx, len(thermal_frames)))
                self.root.update()

            # view state
            self.label_convert_state.config(text=u'共 {} 份檔案 - 已完成'.format(len(thermal_frames)))
            self.root.update()
            Mbox = MessageBox()
            Mbox.info(string=u'Done')


class PreviewComponentAction(PreviewComponentViewer):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    # update with default
    def _update_default(self, img, err):
        try:
            assert isinstance(img, PhotoImage)
        except Exception as e:
            img = err
        return img

    # update component images
    def update(self, fl=None, fr=None, bl=None, br=None, body=None):
        self.photo_cut_fl = self._update_default(fl, self.photo_small)
        self.label_cut_fl.config(image=self.photo_cut_fl)
        self.photo_cut_fr = self._update_default(fr, self.photo_small)
        self.label_cut_fr.config(image=self.photo_cut_fr)
        self.photo_cut_bl = self._update_default(bl, self.photo_small)
        self.label_cut_bl.config(image=self.photo_cut_bl)
        self.photo_cut_br = self._update_default(br, self.photo_small)
        self.label_cut_br.config(image=self.photo_cut_br)
        self.photo_cut_body = self._update_default(body, self.photo_large)
        self.label_cut_body.config(image=self.photo_cut_body)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    entry = EntryThermalComponentAction()
    entry.mainloop()
