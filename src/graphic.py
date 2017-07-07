import os
import cv2
import copy
import logging
import numpy as np

from src.base import BaseGraphCut
from src.filter import savitzky_golay
from src.msg_box import MessageBox
from datetime import datetime
from math import floor
from math import ceil
from math import hypot


class GraphCut(BaseGraphCut):

    def __init__(self, filename, orig_image=None):
        super().__init__(filename)

        # flags & others
        self.__modified = False
        self.__is_body = False
        self.__was_left_draw = False
        self.__is_left_draw = False
        self.__was_right_draw = False
        self.__is_right_draw = False
        self.__is_eliminate = False
        self.__job_queue = []
        self.__contract = True

        # image
        if orig_image is None:
            self.__orig_img = cv2.imread(filename)
        else:
            self.__orig_img = orig_image

        h, w, channel = self.orig_image.shape
        self.__panel_img = self.orig_image.copy()
        self.__transparent = self.generate_transparent((h, w, channel))
        self.__transparent_2x = self.generate_transparent((h*2, w*2, channel))
        self.__output_img = self.__transparent.copy()
        self.__show_img = self.__transparent

        # metadata
        self.__mirror_line = self.generate_mirror_line(self.__orig_img)
        self.__mirror_shift = None

        # tracking label
        self.__eliminate_block = []
        self.__tracking_label = {
            'left': [], 'right': [], 'eliminate': [], 'tmp': []
        }

        # wings color
        __component = {
            'forewings': {'left': None, 'right': None},
            'backwings': {'left': None, 'right': None},
            'body': None
        }
        self.__color_part = copy.deepcopy(__component)
        self.__contour_part = copy.deepcopy(__component)
        self.__contour_rect = copy.deepcopy(__component)
        self.__contour_mask = copy.deepcopy(__component)

        # wings coordinate
        self.__component = {
            'forewings': None, 'backwings': None, 'body': None
        }

    @property
    def orig_image(self):
        return self.__orig_img.copy()

    @property
    def show_image(self):
        filename = 'filename: {}'.format(self.filename.split(os.sep)[-1])
        threshold = 'current threshold: {}'.format(self.THRESHOLD)
        out_image = self.__output_img
        button_y = self.__panel_img.shape[0]-25
        font = cv2.FONT_HERSHEY_TRIPLEX
        fontcolor = self.BLACK
        scale = 0.6

        if out_image is None: out_image = self.__transparent.copy()

        tmp_image = self.__panel_img.copy()
        if self.__contract:
            tmp_image = tmp_image.astype('float64')
            gamma = cv2.getTrackbarPos('Gamma', 'panel')
            tmp_image[:] /= 255
            tmp_image[:] = tmp_image[:]**(gamma/100)
            tmp_image[:] *= 255

        out_image = np.hstack((tmp_image, out_image))
        cv2.putText(out_image, filename, (15, 25), font, scale, fontcolor)
        cv2.putText(out_image, threshold, (15, button_y), font, scale, fontcolor)
        out_image = out_image.astype('uint8')
        return out_image

    @property
    def mirror_line(self):
        return self.__mirror_line

    @mirror_line.setter
    def mirror_line(self, ptx):
        assert isinstance(ptx, tuple) and len(ptx) == 2
        self.__mirror_line = ptx

    @property
    def mirror_shift(self):
        return self.__mirror_shift

    @mirror_shift.setter
    def mirror_shift(self, w):
        assert isinstance(w, int) and w > 0
        self.__mirror_shift = w
        self.__is_body = True

    @property
    def mirror_left_x(self):
        assert self.__mirror_line and self.__mirror_shift
        pt1, pt2 = self.__mirror_line
        shift = self.__mirror_shift
        return pt1[0]-shift

    @property
    def mirror_right_x(self):
        assert self.__mirror_line and self.__mirror_shift
        pt1, pt2 = self.__mirror_line
        shift = self.__mirror_shift
        return pt1[0]+shift

    @property
    def tracking_label(self):
        return self.__tracking_label

    @tracking_label.setter
    def tracking_label(self, label):
        assert isinstance(label, dict)
        assert all([ i in self.__tracking_label.keys() for i in label.keys()])

        self.__tracking_label = label
        self.__tracking_label['tmp'] = []
        if self.__tracking_label[self.LEFT]:
            to_tuple = [tuple(ptx) for ptx in self.__tracking_label[self.LEFT]]
            self.__tracking_label[self.LEFT] = to_tuple
            self.__was_left_draw = True
        if self.__tracking_label[self.RIGHT]:
            to_tuple = [tuple(ptx) for ptx in self.__tracking_label[self.RIGHT]]
            self.__tracking_label[self.RIGHT] = to_tuple
            self.__was_right_draw = True
        if self.__tracking_label['eliminate']:
            track = self.__tracking_label['eliminate']
            to_tuple = [ [tuple(ptx) for ptx in block] for block in track]
            self.__tracking_label['eliminate'] = to_tuple
        self.split_component()

    @property
    def components_color(self):
        return self.__color_part

    @property
    def components_contour(self):
        return self.__contour_part

    @property
    def components(self):
        return self.__component

    def gen_output_image(self):
        try:
            out_image = None
            boundary_y = self.__panel_img.shape[0]
            _coor = lambda x, y: 0 if x is None else x[y]

            out_image_x = 0
            out_image_y = boundary_y
            out_image_bar = 20
            out_image_shift = {'forewings': {}, 'backwings': {}}

            # wings
            for side in [self.LEFT, self.RIGHT]:
                wings = None
                show = False
                merge_y = 0
                alignment_x = max(
                    _coor(self.__contour_rect['forewings'][side], -2),
                    _coor(self.__contour_rect['backwings'][side], -2))

                for part in ['forewings', 'backwings']:
                    coor = self.__component[part]
                    rect = self.__contour_rect[part][side]
                    alignment_y = max(
                        _coor(self.__contour_rect[part][self.LEFT], -1),
                        _coor(self.__contour_rect[part][self.RIGHT], -1))
                    if coor is not None and rect is not None:
                        show = True
                        shift_ptx = self.centralized_rect(
                            rect, (0, 0, alignment_x, alignment_y), part=part)
                        out_image_shift[part][side] = (
                            out_image_x + out_image_bar + shift_ptx[0],
                            out_image_bar + shift_ptx[-1] + merge_y)
                        merge_y += alignment_y

                out_image_x += out_image_bar + alignment_x + out_image_bar
                out_image_y = max(out_image_y, merge_y)

            # body
            coor = self.__component['body']
            rect = self.__contour_rect['body']
            shift_ptx = self.centralized_rect(rect, (0, 0, rect[0], out_image_y))
            if coor is not None and rect is not None and shift_ptx is not None:
                out_image_shift['body'] = (out_image_x + out_image_bar, shift_ptx[-1])
                out_image_x += out_image_bar + shift_ptx[0] + rect[-2]
                out_image_y = max(out_image_y, shift_ptx[-1]+rect[-1])

            # combine
            out_image = self.__transparent_2x[:out_image_y, :out_image_x].copy()
            out_image = out_image.astype('uint8')
            for side in [self.LEFT, self.RIGHT]:
                for part in ['forewings', 'backwings']:
                    x, y, w, h = self.__contour_rect[part][side]
                    X, Y = out_image_shift[part][side]
                    coor = self.__contour_part[part][side]
                    shift_coor = (coor[0]-(y-Y), coor[1]-(x-X))
                    coor_mask, _ = self.filled_component(self.orig_image, coor)

                    shift_y, shift_x = self.matrix_shifting(x-X, y-Y, coor_mask)
                    coor_cond = np.where(coor_mask == 255)
                    out_image[shift_y, shift_x] = self.orig_image[coor_cond]

            x, y, w, h = self.__contour_rect['body']
            X, Y = out_image_shift['body']
            coor = self.__contour_part['body']
            coor_mask, _ = self.filled_component(self.orig_image, coor)
            shift_y, shift_x = self.matrix_shifting(x-X, y-Y, coor_mask)
            coor_cond = np.where(coor_mask == 255)
            out_image[shift_y, shift_x] = self.orig_image[coor_cond]

            # check over size
            if out_image.shape[0] > boundary_y:
                logging.warning('{} not fit in the shape of output image {}'.format(
                    wings.shape, out_image.shape))
                ratio = boundary_y/out_image.shape[0]
                dim = (out_image.shape[1], int(out_image.shape[0]*ratio))
                wings = cv2.resize(wings, dim, interpolation=cv2.INTER_AREA)

            self.__output_img = out_image

        except Exception as e:
            logging.exception('{}'.format(e))
            h, w, channel = self.__output_img.shape
            font = cv2.FONT_HERSHEY_TRIPLEX
            self.__output_img = self.__output_img.astype('float64')
            self.__output_img[:] *= 0.22
            cv2.putText(self.__output_img, 'Error', (int(w/3), int(h/2)), font, 3, self.RED, 3)

    def get_smooth_line(self, track):
        fx, fy = zip(*track)
        fy = np.asarray(fy)
        fy = savitzky_golay(fy, window_size=11, order=4)
        fy = [int(y) for y in fy]
        return list(zip(fx, fy))

    def load_current_instruction(self):
        self.instruction.reset()

        r_description = 'Reset'
        if self.__tracking_label[self.LEFT] or self.__tracking_label[self.RIGHT]:
            r_description = 'Reset all labeling point'
        elif self.__is_body:
            r_description = 'Reset line'

        mouse_left = ''
        mouse_right = ''
        if not self.__is_body:
            mouse_left = 'Get the body width'
        elif not self.__was_left_draw or not self.__was_right_draw:
            mouse_left = 'Separate wings by mirror mode'
            mouse_right = 'Separate connected component'
        else:
            mouse_left = 'Separate wings'
            mouse_right = 'Seperate connected component'

        self.instruction.row_append('ESC', 'Exit')
        self.instruction.row_append('Space', 'Save')
        self.instruction.row_append('r', r_description)
        self.instruction.row_append('q', 'Save & Exit')
        self.instruction.row_append('n', 'Next picture')
        self.instruction.row_append('p', 'Previous picture')
        self.instruction.row_append('u', 'undo eliminate line')
        self.instruction.row_append('y', 'roll back eliminate line')
        self.instruction.row_append('c', 'on/off contract setting')
        self.instruction.row_append('w/UP', 'Increase threshold')
        self.instruction.row_append('s/DOWN', 'Decrease threshold')
        self.instruction.row_append('a/LEFT', 'Move line')
        self.instruction.row_append('d/RIGHT', 'Move line')
        self.instruction.row_append('MOUSE LEFT', mouse_left)
        self.instruction.row_append('MOUSE RIGHT', mouse_right)

    def get_instruction(self, img):
        h, w, channel = img.shape
        line_height = 20
        between_line = 5
        key_esc = 'ESC: Exit'
        key_r = '"r": Reset'
        space = 'Space: Save'
        key_q = '"q": Save and Exit'
        key_n = '"n": next picture'
        key_p = '"p": previous picture'
        key_up = '"w" or UP: + threshold'
        key_down = '"s" or DOWN: - threshold'
        key_left = '"a" or LEFT: Move line'
        key_right = '"d" or RIGHT: Move line'
        mouse_left = 'MOUSE LEFT: '
        mouse_right = None

        if self.__tracking_label[self.LEFT] or self.__tracking_label[self.RIGHT]:
            key_r += ' all labeling point'
        elif self.__is_body:
            key_r += ' line'

        if not self.__is_body:
            mouse_left += 'Get the body width'
        elif not self.__was_left_draw or not self.__was_right_draw:
            mouse_left += 'Separate wings by mirror mode'
            mouse_right = 'MOUSE RIGHT: Separate connected component'
        else:
            mouse_left += 'Separate wings'
            mouse_right = 'MOUSE RIGHT: Seperate connected component'

        instructions = [
            (key_left, key_right, key_up, key_down),
            (key_q, key_r, key_esc, space), (key_n, key_p, '', '')
        ]
        instructions.append((mouse_left, mouse_right) if mouse_right else mouse_left)
        doc_panel = np.zeros(((line_height+between_line)*len(instructions), w, 3))

        for i, instra in enumerate(instructions):
            y = line_height*(i+1) + between_line*i
            font = cv2.FONT_HERSHEY_TRIPLEX
            scale = 0.5
            fontcolor = self.WHITE

            if isinstance(instra, tuple):
                _w = int(w/len(instra))
                for i in range(len(instra)):
                    cv2.putText(
                        doc_panel, instra[i], (10+_w*i, y),
                        font, scale, fontcolor)
            else:
                cv2.putText(doc_panel, instra, (10, y), font , scale, fontcolor)

        return doc_panel

    def get_interp_ptx(self, block):
        block = sorted(block, key=lambda ptx: ptx[0])
        xp = [p[0] for p in block]
        fp = [p[1] for p in block]

        # f = interp1d(xp, fp, kind='linear', copy=False)
        # track = [(
        #     int(x), int(f(x))
        #     ) for x in range(min(xp), max(xp)+1)]

        track = [(
            int(x), int(np.interp(x, xp, fp))
            ) for x in range(min(xp), max(xp)+1)]

        return track

    def get_shape_by_contour(self, contour):
        if not isinstance(contour, np.ndarray):
            contour = self.coor_to_contour(contour)
        return cv2.boundingRect(contour)

    def centralized_rect(self, rect, target, part='forewings'):
        x, y, w, h = rect
        X, Y, W, H = target

        if W < w or H < h: return

        shift_x = (W-w)/2
        shift_y = (H-h)/2

        if part == 'forewings':
            shift_x = floor(shift_x)
            shift_y = floor(shift_y)
        elif part == 'backwings':
            shift_x = ceil(shift_x)
            shift_y = ceil(shift_y)
        else:
            shift_x = int(shift_x)
            shift_y = int(shift_y)

        return (shift_x, shift_y)

    def fixed(self, image, track, mode):
        fixed_img = image.copy()
        erase_img = np.zeros(image.shape)
        __track = sorted(track, key=lambda x: x[0])
        if mode is self.CLEAR_DOWNWARD:
            __track = [(0, __track[0][1])] + __track
            __track = __track + [(fixed_img.shape[1]-1, __track[-1][1])]
        __track = self.get_interp_ptx(__track)

        for ptx in __track:
            x, y = ptx
            if mode is self.CLEAR_UPWARD:
                erase_img[0:y, x] = image[0:y, x].copy()
                erase_img = erase_img.astype('uint8')
                fixed_img[0:y, x] = 255
            elif mode is self.CLEAR_DOWNWARD:
                erase_img[y:, x] = image[y:, x].copy()
                erase_img = erase_img.astype('uint8')
                fixed_img[y:, x] = 255

        return (fixed_img, erase_img)

    def split_component(self):
        '''
        get the connected component by current stat
        '''
        left_track = self.__tracking_label[self.LEFT]
        right_track = self.__tracking_label[self.RIGHT]
        mirror_line_x = self.__mirror_line[0][0]
        bottom_y = lambda track: max([ptx[1] for ptx in track])

        def elimination(image, value):
            for block in self.__tracking_label['eliminate']:
                for i, ptx in enumerate(block):
                    if i == 0: continue
                    cv2.line(image, block[i-1], block[i], value, 2)
            return image

        def get_wings(wings):
            part_wings = cv2.cvtColor(wings, cv2.COLOR_BGR2GRAY)
            ret, threshold = cv2.threshold(
                part_wings, self.THRESHOLD, 255, cv2.THRESH_BINARY_INV)
            part_wings = self.get_component_by(threshold, 1, cv2.CC_STAT_AREA)
            return part_wings

        def save_parts(img, contour, part, side=None, fill=False):

            if fill:
                mask, cnt = self.filled_component(img, contour)
                contour = self.contour_to_coor(cnt[0])

            condition = np.where(mask == 255) if fill else contour
            rect_cnts = cnt[0] if fill else contour

            if side is not None:
                self.__color_part[part][side] = img[condition]
                self.__contour_part[part][side] = contour
                self.__contour_rect[part][side] = self.get_shape_by_contour(rect_cnts)
                self.__contour_mask[part][side] = mask if fill else None
            else:
                self.__color_part[part] = img[condition]
                self.__contour_part[part] = contour
                self.__contour_rect[part] = self.get_shape_by_contour(rect_cnts)
                self.__contour_mask[part] = mask if fill else None

            self.__component[part][condition] = img[condition]
            self.__component[part] = self.__component[part].astype('uint8')

        def init_wings(x, y, side, part):
            wings = self.__orig_img.copy()
            wings = elimination(wings, self.WHITE)

            if side == self.LEFT:
                wings[:, x:] = 255
            elif side == self.RIGHT:
                wings[:, :x] = 255

            if part == 'forewings':
                wings[y:, :] = 255
            elif part == 'backwings':
                wings[:y, :] = 255

            return wings

        def exclude_wings(value, by_mask=False):
            img = self.__orig_img.copy()
            for part in ['forewings', 'backwings']:
                for side in [self.LEFT, self.RIGHT]:
                    if not by_mask and self.__contour_part[part][side]:
                        img[self.__contour_part[part][side]] = value
                    elif by_mask and self.__contour_mask[part][side] is not None:
                        mask = self.__contour_mask[part][side]
                        img[np.where(mask == 255)] = value
            return img

        def process_wings(track, side):
            x = self.__mirror_shift
            x = x if side == self.RIGHT else -x
            x += mirror_line_x
            y = bottom_y(track)

            forewings = init_wings(x, y, side, 'forewings')
            forewings, remained = self.fixed(forewings, track, self.CLEAR_DOWNWARD)
            backwings = init_wings(x, y, side, 'backwings')
            padding = np.where(remained != [0])
            backwings[padding] += remained[padding] - 255

            forepart = get_wings(forewings)
            backpart = get_wings(backwings)

            if forepart is not None:
                save_parts(forewings, forepart, 'forewings', side, True)
            if backpart is not None:
                save_parts(backwings, backpart, 'backwings', side, True)

        if self.__is_body:
            if left_track or right_track:

                self.__component['forewings'] = self.__transparent.copy()
                self.__component['backwings'] = self.__transparent.copy()

                if left_track:
                    process_wings(left_track, self.LEFT)

                if right_track:
                    process_wings(right_track, self.RIGHT)

                if (
                    self.__contour_part['forewings']['left'] and
                    self.__contour_part['forewings']['right'] and
                    self.__contour_part['backwings']['left'] and
                    self.__contour_part['backwings']['right']
                ):
                    self.__component['body'] = self.__transparent.copy()
                    body = exclude_wings(255, by_mask=True)
                    _center = [self.mirror_line[0][0], 0]

                    if self.__tracking_label[self.LEFT]:
                        _left_y = sorted(
                            self.__tracking_label[self.LEFT].copy(),
                            key=lambda x: x[0])
                        _center[-1] += _left_y[-1][-1]
                    if self.__tracking_label[self.RIGHT]:
                        _right_y = sorted(
                            self.__tracking_label[self.RIGHT].copy(),
                            key=lambda x: x[0])
                        _center[-1] += _right_y[0][-1]
                        _center[-1] /= 2 if _center[-1] !=0 else 1
                    elif _center[-1] == 0:
                        _center[-1] = body.shape[0]/2

                    distance = lambda x: hypot(x[0]-_center[0], x[1]-_center[1])
                    bodyparts = cv2.cvtColor(body, cv2.COLOR_BGR2GRAY)
                    ret, threshold = cv2.threshold(
                        bodyparts, self.THRESHOLD, 255, cv2.THRESH_BINARY_INV)

                    output = cv2.connectedComponentsWithStats(threshold, 4, cv2.CV_32S)
                    area_sequence = [(i ,output[2][i][cv2.CC_STAT_AREA]) for i in range(output[0]) if i != 0]
                    area_sequence = sorted(area_sequence, key=lambda x: x[1], reverse=True)
                    area_sequence = area_sequence[:5]
                    area_sequence = [i[0] for i in area_sequence]
                    cond_sequence = [(i ,output[-1][i]) for i in area_sequence]
                    cond_sequence = [(i[0], distance(i[1])) for i in cond_sequence]
                    cond_sequence = sorted(cond_sequence, key=lambda x: x[1])
                    bodyparts = np.where(output[1] == cond_sequence[0][0])

                    if bodyparts is not None: save_parts(body, bodyparts, 'body', fill=True)
                self.gen_output_image()

    def onmouse(self, event, x, y, flags, params):
        h, w, channels = self.__panel_img.shape
        mirror_line_x = self.__mirror_line[0][0]
        point_shift = abs(mirror_line_x - x)
        left_x, right_x = (mirror_line_x - point_shift, mirror_line_x + point_shift)
        side = self.LEFT if x < mirror_line_x else self.RIGHT
        if x > w or y > h: return

        def is_tracking(side):
            self.__tracking_label[side] = []
            if side == self.LEFT:
                self.__is_left_draw = True
                if not self.__was_right_draw:
                    self.__tracking_label[self.RIGHT] = []
            elif side == self.RIGHT:
                self.__is_right_draw = True
                if not self.__was_left_draw:
                    self.__tracking_label[self.LEFT] = []

        def not_tracking(side):
            left_track = self.__tracking_label[self.LEFT]
            right_track = self.__tracking_label[self.RIGHT]

            if side == self.LEFT:
                self.__was_left_draw = True
                self.__is_left_draw = False
            elif side == self.RIGHT:
                self.__was_right_draw = True
                self.__is_right_draw = False

        def valid_tracking(side):
            if side == self.LEFT and 0 < left_x < self.mirror_left_x:
                self.__tracking_label[side].append((left_x, y))
            elif side == self.RIGHT and self.mirror_right_x < right_x < w:
                self.__tracking_label[side].append((right_x, y))
            else:
                not_tracking(side)
                self.__job_queue.append((datetime.now(), self.split_component, 'idle'))

        if event == cv2.EVENT_RBUTTONDOWN:
            self.__modified = True
            self.__is_eliminate = True

        elif event == cv2.EVENT_RBUTTONUP:
            self.__is_eliminate = False
            self.__tracking_label['eliminate'].append(self.__eliminate_block)
            self.__tracking_label['tmp'] = []
            self.__eliminate_block = []
            self.__job_queue.append((datetime.now(), self.split_component, 'idle'))

        elif event == cv2.EVENT_LBUTTONDOWN:
            self.__modified = True
            if self.__is_body:
                if side in [self.LEFT, self.RIGHT]:
                    self.__panel_img = self.__orig_img.copy()
                    is_tracking(side)
                    self.draw()
                else:
                    logging.warning('Not valid region for labeling')

        elif event == cv2.EVENT_LBUTTONUP:
            if not self.__is_body:
                self.__mirror_shift = point_shift
                self.__is_body = True
                self.draw()

            elif self.__is_left_draw or self.__is_right_draw:
                not_tracking(side)

                self.__job_queue.append((datetime.now(), self.split_component, 'idle'))
                self.draw()

        elif event == cv2.EVENT_MOUSEMOVE:

            # body region
            if not self.__is_body:
                self.__panel_img = self.__orig_img.copy()
                cv2.line(self.__panel_img, (left_x, 0), (left_x, h), self.RED, 2)
                cv2.line(self.__panel_img, (right_x, 0), (right_x, h), self.RED, 2)
                self.draw()

            # split forewings and backwings symmetrically
            elif self.__is_left_draw or self.__is_right_draw:
                valid_tracking(side)

                if (
                    side == self.LEFT and
                    self.__is_left_draw and not self.__was_right_draw
                ):
                    valid_tracking(self.RIGHT)
                if (
                    side == self.RIGHT and
                    self.__is_right_draw and not self.__was_left_draw
                ):
                    valid_tracking(self.LEFT)

                self.draw()

            elif self.__is_eliminate:
                if self.__eliminate_block:
                    ix, iy = self.__eliminate_block[-1]
                    cv2.line(self.__panel_img, (ix, iy), (x, y), self.RED, 2)
                self.__eliminate_block.append((x,y))

    def reset(self):
        '''
        reset all metadata and image
        '''
        self.__panel_img = self.__orig_img.copy()

        if (
            self.__was_left_draw or
            self.__was_right_draw or
            self.__tracking_label['eliminate']
        ):
            self.__output_img = None
            self.__was_left_draw = False
            self.__is_left_draw = False
            self.__was_right_draw = False
            self.__is_right_draw = False

            self.__eliminate_block = []
            self.__tracking_label = {
                'left': [], 'right': [], 'eliminate': [], 'tmp': []
            }
            __component = {
                'forewings': {'left': None, 'right': None},
                'backwings': {'left': None, 'right': None},
                'body': None
            }
            self.__color_part = copy.deepcopy(__component)
            self.__contour_part = copy.deepcopy(__component)
            self.__contour_rect = copy.deepcopy(__component)
            self.__contour_mask = copy.deepcopy(__component)
            self.__component = {
                'forewings': None, 'backwings': None, 'body': None
            }

        elif self.__is_body:
            self.__is_body = False
            self.__mirror_shift = None

        self.draw()

    def draw(self):
        '''
        draw all metadata on image
        '''
        h, w, channel = self.__panel_img.shape

        if self.__mirror_line:
            pt1, pt2 = self.__mirror_line
            cv2.line(self.__panel_img, pt1, pt2, self.BLACK, 2)

            if self.__mirror_shift:
                shift = self.__mirror_shift
                l_x, r_x = (pt1[0]-shift, pt1[0]+shift)
                cv2.line(self.__panel_img, (l_x, 0), (l_x, h), self.BLUE, 2)
                cv2.line(self.__panel_img, (r_x, 0), (r_x, h), self.BLUE, 2)

        for side, track in self.__tracking_label.items():
            if side in [self.LEFT, self.RIGHT] and track:
                # if len(track) > 10:
                #     track = self.get_smooth_line(track)
                for i, ptx in enumerate(track):
                    if i == 0: continue
                    cv2.line(self.__panel_img, track[i-1], ptx, self.BLACK, 2)

            elif side == 'eliminate':
                for n, block in enumerate(track):
                    # if len(block) > 10:
                    #     block = self.get_smooth_line(block)
                    for i, ptx in enumerate(block):
                        if i == 0: continue
                        pt1 = block[i-1]
                        cv2.line(self.__panel_img, pt1, ptx, self.RED, 2)

    def run(self):
        '''
        core function to do graph cut
        '''
        self.draw()

        if os.name == 'posix':
            cv2.namedWindow('panel',
                cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        elif os.name == 'nt':
            cv2.namedWindow('panel', cv2.WINDOW_NORMAL + cv2.WINDOW_KEEPRATIO)

        cv2.createTrackbar('Gamma','panel',100, 250, self.null_callback)
        cv2.createTrackbar('Threshold','panel',self.THRESHOLD, 255, self.null_callback)
        cv2.createTrackbar('Refresh','panel',0, 1, self.null_callback)
        cv2.setMouseCallback('panel', self.onmouse)
        logging.info('Begin with STATE={}'.format(self.STATE))

        while True:
            cv2.imshow('panel', self.show_image)
            k = cv2.waitKey(1)

            if os.name == 'nt' and cv2.getWindowProperty('panel', 0) == -1:
                self.STATE = 'exit'
                self.ACTION = 'quit'
                break
            elif k == ord('u'):
                if len(self.__tracking_label['eliminate']) > 0:
                    pop_track = self.__tracking_label['eliminate'][-1]
                    self.__tracking_label['eliminate'] = self.__tracking_label['eliminate'][:-1]
                    self.__tracking_label['tmp'].append(pop_track)
                    self.__panel_img = self.__orig_img.copy()
                    self.draw()
            elif k == ord('y'):
                if len(self.__tracking_label['tmp']) > 0:
                    pop_track = self.__tracking_label['tmp'][-1]
                    self.__tracking_label['eliminate'].append(pop_track)
                    self.__tracking_label['tmp'] = self.__tracking_label['tmp'][:-1]
                    self.__panel_img = self.__orig_img.copy()
                    self.draw()
            elif k == ord('c'):
                self.__contract = not self.__contract
            elif k == ord('h'):
                self.load_current_instruction()
                self.instruction.show()
            elif k == 27:
                self.STATE = 'exit'
                self.ACTION = 'quit'
                break
            elif k == ord(' '):
                self.STATE = 'done'
                self.ACTION = 'save'
                break
            elif k == ord('q'):
                self.STATE = 'pause'
                self.ACTION = 'save'
                break
            elif k == ord('n'):
                self.ACTION = 'next'
                if self.__modified:
                    MBox = MessageBox()
                    want_save = MBox.ask_ques()
                    if want_save: self.STATE = 'pause'
                    else: break
                break
            elif k == ord('p'):
                self.ACTION = 'previous'
                if self.__modified:
                    MBox = MessageBox()
                    want_save = MBox.ask_ques()
                    if want_save: self.STATE = 'pause'
                    else: break
                break
            elif k == self.KEY_UP or k == ord('w'):
                while True:
                    check_k = cv2.waitKey(200)
                    if check_k == self.KEY_UP or check_k == ord('w'):
                        self.THRESHOLD = min(self.THRESHOLD+1, 254)
                        pass
                    else:
                        break
                if self.THRESHOLD + 1 >= 255:
                    MBox = MessageBox()
                    warn = MBox.alert(
                        title='Warning',
                        string='Please set threshold between 1~254')
                    continue
                self.__modified = True
                self.THRESHOLD += 1
                cv2.setTrackbarPos('Threshold', 'panel', self.THRESHOLD)
                self.__job_queue.append((datetime.now(), self.split_component, 'idle'))
            elif k == self.KEY_DOWN or k == ord('s'):
                while True:
                    check_k = cv2.waitKey(200)
                    if check_k == self.KEY_DOWN or check_k == ord('s'):
                        self.THRESHOLD = min(self.THRESHOLD-1, 254)
                        pass
                    else:
                        break
                if self.THRESHOLD - 1 <= 0:
                    MBox = MessageBox()
                    warn = MBox.alert(
                        title='Warning',
                        string='Please set threshold between 1~254')
                    continue
                self.__modified = True
                self.THRESHOLD -= 1
                cv2.setTrackbarPos('Threshold', 'panel', self.THRESHOLD)
                self.__job_queue.append((datetime.now(), self.split_component, 'idle'))
            elif k == ord('r'):
                self.__modified = True
                self.reset()
            elif k == self.KEY_LEFT or k == ord('a'):
                if self.__was_left_draw or self.__was_right_draw: continue
                self.__modified = True
                pt1, pt2 = self.__mirror_line
                pt1 = (pt1[0]-1, pt1[1])
                pt2 = (pt2[0]-1, pt2[1])
                self.__mirror_line = (pt1, pt2)
                self.__panel_img = self.__orig_img.copy()
                self.draw()
            elif k == self.KEY_RIGHT or k == ord('d'):
                if self.__was_left_draw or self.__was_right_draw: continue
                self.__modified = True
                pt1, pt2 = self.__mirror_line
                pt1 = (pt1[0]+1, pt1[1])
                pt2 = (pt2[0]+1, pt2[1])
                self.__mirror_line = (pt1, pt2)
                self.__panel_img = self.__orig_img.copy()
                self.draw()

            threshold = cv2.getTrackbarPos('Threshold', 'panel')
            switch = cv2.getTrackbarPos('Refresh', 'panel')

            if switch:
                if threshold == 0:
                    cv2.setTrackbarPos('Threshold', 'panel', 1)
                elif threshold == 255:
                    cv2.setTrackbarPos('Threshold', 'panel', 254)
                elif threshold != self.THRESHOLD:
                    self.THRESHOLD = threshold
                    self.__job_queue.append((datetime.now(), self.split_component, 'idle'))

            # handle heavy job
            if self.__job_queue:
                if len(self.__job_queue) == 1:
                    date, func, state = self.__job_queue[0]
                    if state == 'idle':
                        func()
                        self.__job_queue[0] = (date, func, 'done')
                else:
                    done_queue = [ i for i in self.__job_queue if i[-1] == 'done']
                    done_obj = done_queue[-1] if done_queue else None
                    idle_queue = [ i for i in self.__job_queue if i[-1] == 'idle']
                    idle_obj = idle_queue[-1] if idle_queue else None

                    if done_obj and idle_obj:
                        timedelta = idle_obj[0] - done_obj[0]
                        if timedelta.total_seconds() > 0.5:
                            date, func, state = idle_obj
                            func()
                            self.__job_queue = [(date, func, 'done')]
                        else:
                            date, func, state = idle_obj
                            self.__job_queue = [done_obj, (datetime.now(), func, state)]
                    elif not done_obj and idle_obj:
                        date, func, state = idle_obj
                        func()
                        self.__job_queue = [(date, func, 'done')]

        logging.info('End with STATE={}'.format(self.STATE))
        cv2.destroyAllWindows()
