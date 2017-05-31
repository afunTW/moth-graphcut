import os
import cv2
import math
import logging
import numpy as np

from scipy.spatial.distance import cosine
from src.filter import savitzky_golay


class GraphCut(object):
    '''
    ===============================================================================
    Interactive Image Segmentation

    This sample shows interactive image segmentation using grabcut algorithm.

    README FIRST:
        Two windows will show up, one for input and one for output.

    Key 'Esc' - To exit the program
    Key 'r' - To reset the setup
    Key 'a', '->' - Shift mirror line to left side
    Key 'd', '<-' - Shift mirror line to right side
    ===============================================================================
    '''
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

        if os.name == 'posix':
            self.KEY_LEFT = 81
            self.KEY_RIGHT = 83
        elif os.name == 'nt':
            self.KEY_LEFT = 2424832
            self.KEY_RIGHT = 2555904

        # flags & others
        self.__transparent_bg = None
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
        self.__show_img = self.gen_transparent_bg(self.__orig_img)

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

        # wings coordinate
        self.__component = {
            'forewings': None, 'backwings': None, 'body': None
        }

    @property
    def orig_image(self):
        return self.__orig_img.copy()

    @property
    def show_image(self):
        output_image = self.gen_transparent_bg(self.__panel_img)
        parts = ['body','forewings', 'backwings']
        boundary = None

        for part in parts:
            coor = self.__component[part]
            contour = self.__contour_part[part]

            if part == 'body' and coor is not None and contour is not None:
                x, y, w, h = self.get_shape_by_contour(contour)
                H = coor.shape[0]
                output_image[0:H, 5:5+w] = coor[0:H, x:x+w]
                output_image = output_image.astype('uint8')
                boundary = (0, 5+w)
                continue

            for side in [self.ON_LEFT, self.ON_RIGHT]:
                # print(self.__contour_part)
                if contour is None: break
                if contour[side] is None: continue
                x, y, w, h = self.get_shape_by_contour(contour[side])
                X = boundary[1] if side == self.ON_LEFT else output_image.shape[1]
                Y = boundary[0] if part == 'forewings' else output_image.shape[0]
                if part == 'forewings' and side == self.ON_LEFT:
                    output_image[Y+5:Y+5+h, X:X+w] = coor[y:y+h, x:x+w]
                elif part == 'forewings' and side == self.ON_RIGHT:
                    output_image[Y+5:Y+5+h, X-w:X] = coor[y:y+h, x:x+w]
                elif part == 'backwings' and side == self.ON_LEFT:
                    output_image[Y-5-h:Y-5, X:X+w] = coor[y:y+h, x:x+w]
                elif part == 'backwings' and side == self.ON_RIGHT:
                    output_image[Y-5-h:Y-5, X-w:X] = coor[y:y+h, x:x+w]

        output_image = np.hstack((self.__panel_img.copy(), output_image))
        instructions = self.get_instruction(output_image)
        output_image = np.vstack((output_image, instructions))
        output_image = output_image.astype('uint8')
        return output_image

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

    def gen_transparent_bg(self, image):
        '''
        generate transparents background
        '''
        # assert isinstance(shape, tuple) and len(shape) == 3
        img = np.zeros(image.shape) * 255
        h, w, channel = img.shape
        _col = [False, True] * math.ceil((w/2))
        _row = [_col[1:], _col[:-1]] * int(h/2)

        if h % 2: _row.append(_col[1:])
        _mat = _row
        _mat = np.array(_mat)

        img[_mat] = 125
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
        key_esc = 'Key "Esc": Exit the image operation'
        key_r = 'Key "r": Reset'
        key_s = 'Ket "s": Save the result of graph cut'
        key_left = 'Key "a" or "<-": Shifting mirror line to the left'
        key_right = 'Key "d" or "->": Shifting mirror line to the right'
        mouse_left = 'Mouse click left: '
        mouse_right = None

        if self.__tracking_label[self.ON_LEFT] or self.__tracking_label[self.ON_RIGHT]:
            key_r += ' all labeling point'
        elif self.__is_body:
            key_r += ' mirror line'

        if not self.__is_body:
            mouse_left += 'Determine the body width'
        elif not self.__was_left_draw or not self.__was_right_draw:
            mouse_left += 'Separate fore and back wings in mirror mode'
            mouse_right = 'Mouse click right: Seperate connected component'
        else:
            mouse_left += 'Separate fore and back wings'
            mouse_right = 'Mouse click right: Seperate connected component'

        instructions = [(key_esc, key_r), key_s, key_left, key_right, mouse_left]
        mouse_right and instructions.append(mouse_right)
        doc_panel = np.zeros(((line_height+between_line)*len(instructions), w, 3))

        for i, instra in enumerate(instructions):
            y = line_height*(i+1) + between_line*i
            font = cv2.FONT_HERSHEY_TRIPLEX
            scale = 0.5
            fontcolor = self.WHITE

            if isinstance(instra, tuple):
                cv2.putText(doc_panel, instra[0], (10, y), font, scale, fontcolor)
                cv2.putText(doc_panel, instra[1], (int(w/2), y), font, scale, fontcolor)
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
        assert 0 < nth < output[0]

        cond_sequence = [(i ,output[2][i][by]) for i in range(output[0]) if i != 0]
        cond_sequence = sorted(cond_sequence, key=lambda x: x[1], reverse=True)
        return np.where(output[1] == cond_sequence[nth-1][0])

    def get_shape_by_contour(self, contour):
        contour = list(zip(contour[1], contour[0]))
        cnt = np.zeros(shape=(len(contour), 1, 2))
        for i in range(len(contour)): cnt[i] = contour[i]
        cnt = cnt.astype('int32')
        return cv2.boundingRect(cnt)

    def fixed(self, image, track, mode):
        fixed_img = image.copy()
        erase_img = np.zeros(image.shape)
        track = self.get_interp_ptx(track)

        for ptx in track:
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
            ret, threshold = cv2.threshold(part_wings, 250, 255, cv2.THRESH_BINARY_INV)
            part_wings = self.get_component_by(threshold, 1, cv2.CC_STAT_AREA)
            return part_wings

        def save_wings(img, contour, side, part):
            self.__color_part[part][side] = img[contour]
            self.__contour_part[part][side] = contour
            self.__component[part][contour] = img[contour]
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

        def exclude_wings(value):
            img = self.__orig_img.copy()
            for part in ['forewings', 'backwings']:
                for side in [self.ON_LEFT, self.ON_RIGHT]:
                    img[self.__contour_part[part][side]] = value
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
            save_wings(forewings, forepart, side, 'forewings')
            save_wings(backwings, backpart, side, 'backwings')

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
                    body = exclude_wings(255)
                    bodyparts = cv2.cvtColor(body, cv2.COLOR_BGR2GRAY)
                    ret, threshold = cv2.threshold(bodyparts, 250, 255, cv2.THRESH_BINARY_INV)
                    bodyparts = self.get_component_by(threshold, 1, cv2.CC_STAT_AREA)
                    self.__color_part['body'] = body[bodyparts]
                    self.__contour_part['body'] = bodyparts
                    self.__component['body'][bodyparts] = body[bodyparts]
                    self.__component['body'] = self.__component['body'].astype('uint8')

    def onmouse(self, event, x, y, flags, params):
        h, w, channels = self.__panel_img.shape
        mirror_line_x = self.__mirror_line[0][0]
        point_shift = abs(mirror_line_x - x)
        left_x, right_x = (mirror_line_x - point_shift, mirror_line_x + point_shift)
        side = self.ON_LEFT if x < mirror_line_x else self.ON_RIGHT

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
            self.__is_eliminate = True

        elif event == cv2.EVENT_RBUTTONUP:
            self.__is_eliminate = False
            self.__tracking_label['eliminate'].append(self.__eliminate_block)
            self.__eliminate_block = []
            self.split_component()

        elif event == cv2.EVENT_LBUTTONDOWN:
            if self.__is_body:
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
                if len(track) > 10:
                    track = self.get_smooth_line(track)
                for i, ptx in enumerate(track):
                    if i == 0: continue
                    cv2.line(self.__panel_img, track[i-1], ptx, self.BLACK, 2)

            elif side == 'eliminate':
                for n, block in enumerate(track):
                    if len(block) > 10:
                        block = self.get_smooth_line(block)
                    for i, ptx in enumerate(block):
                        if i == 0: continue
                        pt1 = block[i-1]
                        cv2.line(self.__panel_img, pt1, ptx, self.RED, 2)

    def run(self):
        '''
        core function to do graph cut
        '''
        self.draw()
        cv2.namedWindow('displayed')

        if os.name == 'posix':
            cv2.namedWindow('panel',
                cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        elif os.name == 'nt':
            cv2.namedWindow('panel', cv2.WINDOW_KEEPRATIO)

        cv2.setMouseCallback('panel', self.onmouse)
        cv2.moveWindow('panel', self.__panel_img.shape[1]+10, 0)

        while True:
            instructions = self.get_instruction(self.__panel_img)
            panel_image = np.vstack((self.__panel_img, instructions))
            panel_image = panel_image.astype('uint8')
            cv2.imshow('displayed', self.show_image)
            cv2.imshow('panel', panel_image)
            k = cv2.waitKey(1)

            if k == 27:
                self.STATE = 'pause'
                break
            elif k == ord('s'):
                self.STATE = 'done'
                break
            elif k == ord('r'):
                self.reset()
            elif k == self.KEY_LEFT or k == ord('a'):
                # left
                pt1, pt2 = self.__mirror_line
                pt1 = (pt1[0]-1, pt1[1])
                pt2 = (pt2[0]-1, pt2[1])
                self.__mirror_line = (pt1, pt2)
                self.__panel_img = self.__orig_img.copy()
                self.draw()
            elif k == self.KEY_RIGHT or k == ord('d'):
                # right
                pt1, pt2 = self.__mirror_line
                pt1 = (pt1[0]+1, pt1[1])
                pt2 = (pt2[0]+1, pt2[1])
                self.__mirror_line = (pt1, pt2)
                self.__panel_img = self.__orig_img.copy()
                self.draw()

        cv2.destroyAllWindows()
