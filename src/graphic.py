import os
import cv2
import logging
import numpy as np

from scipy.spatial.distance import cosine
from src.msg_box import MessageBox
from src.filter import savitzky_golay
from math import floor
from math import ceil
from math import hypot


class GraphCut(object):

    def __init__(self, filename, orig_image=None):
        self.filename = filename
        self.BLUE = [255,0,0]
        self.RED = [0,0,255]
        self.GREEN = [0,255,0]
        self.BLACK = [0,0,0]
        self.WHITE = [255,255,255]

        self.CLEAR_UPWARD = {'color': self.BLACK}
        self.CLEAR_DOWNWARD = {'color': self.BLACK}
        self.ON_LEFT = 'left'
        self.ON_RIGHT = 'right'
        self.STATE = 'none'
        self.ACTION = 'save'
        self.THRESHOLD = 250

        if os.name == 'posix':
            self.KEY_LEFT = 81
            self.KEY_UP = 82
            self.KEY_RIGHT = 83
            self.KEY_DOWN = 84
        elif os.name == 'nt':
            self.KEY_LEFT = 2424832
            self.KEY_UP = 2490368
            self.KEY_RIGHT = 2555904
            self.KEY_DOWN = 2621440

        # flags & others
        self.__transparent_bg = None
        self.__modified = False
        self.__is_body = False
        self.__was_left_draw = False
        self.__is_left_draw = False
        self.__was_right_draw = False
        self.__is_right_draw = False
        self.__is_eliminate = False

        # image
        if orig_image is None:
            self.__orig_img = cv2.imread(filename)
        else:
            self.__orig_img = orig_image

        self.__panel_img = self.__orig_img.copy()
        self.__output_img = None
        self.__show_img = self.gen_transparent_bg(self.__orig_img.shape)

        # metadata
        self.__mirror_line = self.gen_mirror_line(self.__orig_img)
        self.__mirror_shift = None

        # tracking label
        self.__eliminate_block = []
        self.__tracking_label = {
            'left': [], 'right': [], 'eliminate': []
        }

        # wings color
        self.__color_part = {
            'forewings': {'left': None, 'right': None},
            'backwings': {'left': None, 'right': None},
            'body': None
        }

        # wings contour
        self.__contour_part = {
            'forewings': {'left': None, 'right': None},
            'backwings': {'left': None, 'right': None},
            'body': None
        }
        self.__contour_rect = {
            'forewings': {'left': None, 'right': None},
            'backwings': {'left': None, 'right': None},
            'body': None
        }
        self.__contour_mask = {
            'forewings': {'left': None, 'right': None},
            'backwings': {'left': None, 'right': None},
            'body': None
        }

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

        if out_image is None: out_image = self.__transparent_bg.copy()
        out_image = np.hstack((self.__panel_img.copy(), out_image))
        instructions = self.get_instruction(out_image)
        out_image = np.vstack((out_image, instructions))
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
        if self.__tracking_label[self.ON_LEFT]:
            to_tuple = [tuple(ptx) for ptx in self.__tracking_label[self.ON_LEFT]]
            self.__tracking_label[self.ON_LEFT] = to_tuple
            self.__was_left_draw = True
        if self.__tracking_label[self.ON_RIGHT]:
            to_tuple = [tuple(ptx) for ptx in self.__tracking_label[self.ON_RIGHT]]
            self.__tracking_label[self.ON_RIGHT] = to_tuple
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

    def __coor_to_contour(self, coor):
        cnt = list(coor)
        cnt.reverse()
        cnt = np.array(cnt)
        cnt = cnt.transpose()
        cnt = cnt.reshape((cnt.shape[0], 1, 2))
        cnt = cnt.astype('int32')
        return cnt

    def __contour_to_coor(self, contour):
        coor = contour.reshape(contour.shape[0], 2)
        coor = coor.transpose()
        coor = coor.tolist()
        coor = [np.array(i) for i in coor]
        coor.reverse()
        coor = tuple(coor)
        return coor

    def gen_transparent_bg(self, shape):
        '''
        generate transparents background
        '''
        img = np.zeros(shape) * 255
        img[::2, ::2] = 255
        img[1::2, 1::2] = 255
        self.__transparent_bg = img
        return img

    def gen_mirror_line(self, image, scope=10):
        '''
        generate mirror line when initial
        '''
        img = image.copy()
        h, w, _ = img.shape
        line_x = int(w/2)
        approach_x = [line_x]

        while True:
            max_similarity = None

            for x in range(line_x-scope, line_x+scope):
                min_w = min(x, w-x)
                sim = cosine(
                   img[0:h, x-min_w:x].flatten(),
                    np.fliplr(img[0:h, x:x+min_w].copy()).flatten())

                if max_similarity is None or sim > max_similarity[1]:
                    max_similarity = (x, sim)

            if max_similarity[0] == line_x: break
            else: line_x = max_similarity[0]

        logging.info('generate mirror line {0}'.format(((line_x, 0), (line_x, h))))
        return ((line_x, 0), (line_x, h))

    def gen_output_image(self):
        out_image = None
        hsave = lambda x, y: y if x is None else np.hstack((x, y))
        vsave = lambda x, y: y if x is None else np.vstack((x, y))
        _coor = lambda x, y: 0 if x is None else x[y]
        boundary_y = self.__panel_img.shape[0]
        bar = self.__transparent_bg[0:boundary_y, 0:20]

        # combind body
        coor = self.__component['body']
        rect = self.__contour_rect['body']
        if coor is not None and rect is not None:
            x, y, w, h = rect
            out_image = hsave(out_image, bar)
            out_image = hsave(out_image, coor[0:boundary_y, x:x+w])
            out_image = hsave(out_image, bar)
            out_image = out_image.astype('uint8')

        # combine wings
        alignment_y = max(
            _coor(self.__contour_rect['forewings'][self.ON_LEFT], -1),
            _coor(self.__contour_rect['forewings'][self.ON_RIGHT], -1))

        for side in [self.ON_LEFT, self.ON_RIGHT]:
            wings = None
            show = False
            alignment_x = max(
                _coor(self.__contour_rect['forewings'][side], -2),
                _coor(self.__contour_rect['backwings'][side], -2))

            for part in ['forewings', 'backwings']:
                coor = self.__component[part]
                rect = self.__contour_rect[part][side]
                if coor is not None and rect is not None:
                    show = True
                    x, y, w, h = rect
                    wing = self.transparent_padding(
                        alignment_x, h, coor[y:y+h, x:x+w])
                    wings = vsave(wings, self.__transparent_bg[0:20, 0:alignment_x])
                    wings = vsave(wings, wing)

            wings = self.transparent_padding(alignment_x, boundary_y, wings)
            if wings.shape[0] != boundary_y:
                logging.warning('{} not fit in the shape of output image {}'.format(
                    wings.shape, out_image.shape))
                ratio = boundary_y/wings.shape[0]
                dim = (wings.shape[1], int(wings.shape[0]*ratio))
                wings = cv2.resize(wings, dim, interpolation=cv2.INTER_AREA)

            if show:
                out_image = hsave(out_image, bar)
                out_image = hsave(out_image, wings)
        self.__output_img = out_image

    def get_smooth_line(self, track):
        fx, fy = zip(*track)
        fy = np.asarray(fy)
        fy = savitzky_golay(fy, window_size=11, order=4)
        fy = [int(y) for y in fy]
        return list(zip(fx, fy))

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
        key_up = '"w" or UP: increase threshold'
        key_down = '"s" or DOWN: decrease threshold'
        key_left = '"a" or LEFT: Shifting line to the left'
        key_right = '"d" or RIGHT: Shifting line to the right'
        mouse_left = 'MOUSE LEFT: '
        mouse_right = None

        if self.__tracking_label[self.ON_LEFT] or self.__tracking_label[self.ON_RIGHT]:
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
        # mouse_right and instructions.append(mouse_right)
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
                # cv2.putText(doc_panel, instra[0], (10, y), font, scale, fontcolor)
                # cv2.putText(doc_panel, instra[1], (int(w/2), y), font, scale, fontcolor)
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

    def get_component_by(self, threshold, nth, by):
        '''
        return nth connected component by the value in stat matrix
        in descending sequences
            cv2.CC_STAT_LEFT The leftmost (x) coordinate
            cv2.CC_STAT_TOP The topmost (y) coordinate
            cv2.CC_STAT_WIDTH The horizontal size of the bounding box
            cv2.CC_STAT_HEIGHT The vertical size of the bounding box
            cv2.CC_STAT_AREA The total area (in pixels) of the connected component
        '''
        output = cv2.connectedComponentsWithStats(threshold, 4, cv2.CV_32S)
        assert by in [
            cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP,
            cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT, cv2.CC_STAT_AREA]
        if 0 >= nth or nth >= output[0]: return

        cond_sequence = [(i ,output[2][i][by]) for i in range(output[0]) if i != 0]
        cond_sequence = sorted(cond_sequence, key=lambda x: x[1], reverse=True)
        return np.where(output[1] == cond_sequence[nth-1][0])

    def get_filled_component(self, img, contour):
        cmp_img = np.zeros_like(img)
        cmp_img[contour] = img[contour]
        cmp_img = cv2.cvtColor(cmp_img, cv2.COLOR_BGR2GRAY)
        cmp_img, cnt, hierarchy = cv2.findContours(
            cmp_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cmp_img = np.zeros_like(cmp_img)
        cv2.drawContours(cmp_img, cnt, -1, 255, -1)
        return cmp_img, cnt

    def get_shape_by_contour(self, contour):
        if not isinstance(contour, np.ndarray):
            contour = self.__coor_to_contour(contour)
        return cv2.boundingRect(contour)

    def transparent_padding(self, x, y, img):
        padding = self.__transparent_bg.copy()
        Y, X, _ = padding.shape
        gener = lambda x, y: self.gen_transparent_bg((y, x, 3))
        check = lambda x, y, bg: genre(x, y) if Y < y or X < x else bg
        if img is None: return check(x, y, padding)

        h, w, _ = img.shape
        if h >= y and w >= x: return img

        if h < y:
            padding = check(w, ceil((y-h)/2), padding)
            Y, X, _ = padding.shape
            img = np.vstack((
                padding[0:floor((y-h)/2), 0:w],
                img,
                padding[0:ceil((y-h)/2), 0:w]))
            h, w, _ = img.shape

        if w < x:
            padding = check(ceil((x-w)/2), h, padding)
            Y, X, _ = padding.shape
            img = np.hstack((
                padding[0:h, 0:floor((x-w)/2)],
                img,
                padding[0:h, 0:ceil((x-w)/2)]))
            h, w, _ = img.shape
        return img

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
        left_track = self.__tracking_label[self.ON_LEFT]
        right_track = self.__tracking_label[self.ON_RIGHT]
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
                mask, cnt = self.get_filled_component(img, contour)
                contour = self.__contour_to_coor(cnt[0])

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

            if side == self.ON_LEFT:
                wings[:, x:] = 255
            elif side == self.ON_RIGHT:
                wings[:, :x] = 255

            if part == 'forewings':
                wings[y:, :] = 255
            elif part == 'backwings':
                wings[:y, :] = 255

            return wings

        def exclude_wings(value, by_mask=False):
            img = self.__orig_img.copy()
            for part in ['forewings', 'backwings']:
                for side in [self.ON_LEFT, self.ON_RIGHT]:
                    if not by_mask and self.__contour_part[part][side]:
                        img[self.__contour_part[part][side]] = value
                    elif by_mask and self.__contour_mask[part][side] is not None:
                        mask = self.__contour_mask[part][side]
                        img[np.where(mask == 255)] = value
            return img

        def process_wings(track, side):
            x = self.__mirror_shift
            x = x if side == self.ON_RIGHT else -x
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

                self.__component['forewings'] = self.__transparent_bg.copy()
                self.__component['backwings'] = self.__transparent_bg.copy()

                if left_track:
                    process_wings(left_track, self.ON_LEFT)

                if right_track:
                    process_wings(right_track, self.ON_RIGHT)

                if (
                    self.__contour_part['forewings']['left'] and
                    self.__contour_part['forewings']['right'] and
                    self.__contour_part['backwings']['left'] and
                    self.__contour_part['backwings']['right']
                ):
                    self.__component['body'] = self.__transparent_bg.copy()
                    body = exclude_wings(255, by_mask=True)
                    _center = (body.shape[1]/2, body.shape[0]/2)
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

                    if bodyparts is not None: save_parts(body, bodyparts, 'body')
                self.gen_output_image()

    def onmouse(self, event, x, y, flags, params):
        h, w, channels = self.__panel_img.shape
        mirror_line_x = self.__mirror_line[0][0]
        point_shift = abs(mirror_line_x - x)
        left_x, right_x = (mirror_line_x - point_shift, mirror_line_x + point_shift)
        side = self.ON_LEFT if x < mirror_line_x else self.ON_RIGHT
        if x > w or y > h: return

        def is_tracking(side):
            self.__tracking_label[side] = []
            if side == self.ON_LEFT:
                self.__is_left_draw = True
                if not self.__was_right_draw:
                    self.__tracking_label[self.ON_RIGHT] = []
            elif side == self.ON_RIGHT:
                self.__is_right_draw = True
                if not self.__was_left_draw:
                    self.__tracking_label[self.ON_LEFT] = []

        def not_tracking(side):
            left_track = self.__tracking_label[self.ON_LEFT]
            right_track = self.__tracking_label[self.ON_RIGHT]

            if side == self.ON_LEFT:
                self.__was_left_draw = True
                self.__is_left_draw = False
            elif side == self.ON_RIGHT:
                self.__was_right_draw = True
                self.__is_right_draw = False

        def valid_tracking(side):
            if side == self.ON_LEFT and 0 < left_x < self.mirror_left_x:
                self.__tracking_label[side].append((left_x, y))
            elif side == self.ON_RIGHT and self.mirror_right_x < right_x < w:
                self.__tracking_label[side].append((right_x, y))
            else:
                not_tracking(side)
                self.split_component()

        if event == cv2.EVENT_RBUTTONDOWN:
            self.__modified = True
            self.__is_eliminate = True

        elif event == cv2.EVENT_RBUTTONUP:
            self.__is_eliminate = False
            self.__tracking_label['eliminate'].append(self.__eliminate_block)
            self.__eliminate_block = []
            self.split_component()

        elif event == cv2.EVENT_LBUTTONDOWN:
            if self.__is_body:
                self.__modified = True
                if side in [self.ON_LEFT, self.ON_RIGHT]:
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

                self.split_component()
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
                    side == self.ON_LEFT and
                    self.__is_left_draw and not self.__was_right_draw
                ):
                    valid_tracking(self.ON_RIGHT)
                if (
                    side == self.ON_RIGHT and
                    self.__is_right_draw and not self.__was_left_draw
                ):
                    valid_tracking(self.ON_LEFT)

                self.draw()

            if self.__is_eliminate:
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
                'left': [], 'right': [], 'eliminate': []
            }
            self.__color_part = {
                'forewings': {'left': None, 'right': None},
                'backwings': {'left': None, 'right': None},
                'body': None
            }
            self.__contour_part = {
                'forewings': {'left': None, 'right': None},
                'backwings': {'left': None, 'right': None},
                'body': None
            }
            self.__contour_rect = {
                'forewings': {'left': None, 'right': None},
                'backwings': {'left': None, 'right': None},
                'body': None
            }
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
            if side in [self.ON_LEFT, self.ON_RIGHT] and track:
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

        cv2.setMouseCallback('panel', self.onmouse)
        logging.info('Begin with STATE={}'.format(self.STATE))

        while True:
            cv2.imshow('panel', self.show_image)
            k = cv2.waitKey(1)

            if os.name == 'nt' and cv2.getWindowProperty('panel', 0) == -1:
                self.STATE = 'exit'
                self.ACTION = 'quit'
                break
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
                break
            elif k == ord('p'):
                self.ACTION = 'previous'
                if self.__modified:
                    MBox = MessageBox()
                    want_save = MBox.ask_ques()
                    if want_save: self.STATE = 'pause'
                break
            elif k == self.KEY_UP or k == ord('w'):
                if self.THRESHOLD + 1 > 255: continue
                self.__modified = True
                self.THRESHOLD += 1
                self.split_component()
            elif k == self.KEY_DOWN or k == ord('s'):
                if self.THRESHOLD - 1 < 0: continue
                self.__modified = True
                self.THRESHOLD -= 1
                self.split_component()
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

        cv2.destroyAllWindows()
