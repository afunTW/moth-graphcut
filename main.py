import os
import sys
import cv2
import json
import glob
import logging
import argparse
import numpy as np

from hashlib import sha1
from src import detector
from src import graphic


def argparser():
    parser = argparse.ArgumentParser(description='interactive graph cut for moth image')
    parser.add_argument('-a', '--all', help='process all image',
        action='store_true', default=False)
    parser.add_argument('-i', '--image', help='process input image',
        nargs='+', default=[])
    parser.add_argument('-r', '--recursive', help='process all image in given directory',
        nargs='+', default=[])
    return parser

def filter_rects(rects, ignore_rect):
    result = []
    ix, iy, iw, ih = ignore_rect

    for rect in rects:
        x, y, w, h = rect
        if ix<x<x+w<ix+iw and iy<y<y+h<iy+ih: continue
        else: result.append(rect)

    return result

def is_bottom_right(rects):
    result = None
    for rect in rects:
        if not result or (rect[0]+rect[2]) >= (result[0]+result[2]):
            result = rect
            continue
    return result

def graph_cut(filename, template=None, last_status=None):

    # filter
    orig_image = None
    if template:
        logging.info(' Process scale filter')
        scale_detector = detector.ShapeDetector(template, filename)
        scale_detector.detect_template()
        orig_image = scale_detector.output

        if scale_detector.template_result:
            logging.info('  * Filter template')
            tx, ty, tw, th = scale_detector.template_result
            H, W, channels = scale_detector.output.shape
            scale_detector.detect_retangle(focus_rect=(0, ty, W, H-ty))

            scale_rects = filter_rects(
                scale_detector.rectangles, scale_detector.template_result)
            rect = is_bottom_right(scale_rects)

            x, y, w, h = scale_detector.template_result
            orig_image[y:y+h, x:x+w, :] = 255

            if rect:
                logging.info('  * Filter scale')
                x, y, w, h = rect
                orig_image[y-5:y+h+5, x-5:x+w+5, :] = 255

    # graphic
    gc = graphic.GraphCut(filename, orig_image=orig_image)
    logging.info(' Process graph cut')

    if last_status:
        logging.info(' Rollback to last status')

        if last_status['mirror_line']:
            pt1 , pt2 = last_status['mirror_line']
            gc.mirror_line = (tuple(pt1), tuple(pt2))

        if last_status['mirror_shift']:
            gc.mirror_shift = last_status['mirror_shift']

        if last_status['threshold']:
            gc.THRESHOLD = last_status['threshold']

        if last_status['state']:
            gc.STATE = last_status['state']

        if any([v for v in last_status['tracking_label']]):
            gc.tracking_label = last_status['tracking_label']

        gc.STATE = last_status['state']

    gc.run()

    return gc

def all_to_list(f):
    assert isinstance(f, dict)

    for k, v in f.items():
        if isinstance(v, dict):
            f.update({k: all_to_list(v)})
        elif isinstance(v, np.ndarray):
            f.update({k: v.tolist()})
        elif isinstance(v, tuple):
            v = tuple(i.tolist() if isinstance(i, np.ndarray) else i for i in v)
            f.update({k: v})
        else:
            print('Not support {} in the type of {}'.format(k, type(v)))

    return f

def saved_metadata(gc, saved_file):

    dirpath = os.path.join(os.sep.join(saved_file.split(os.sep)[:-1]))
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    data = {
        'name': gc.filename,
        'state': gc.STATE,
        'gamma': gc.gamma,
        'mirror_line': gc.mirror_line,
        'mirror_shift': gc.mirror_shift,
        'tracking_label': gc.tracking_label,
        'threshold': gc.THRESHOLD,
        'components_color': all_to_list(gc.components_color.copy()),
        'components_contour': all_to_list(gc.components_contour.copy())
    }

    with open(saved_file, 'w+') as f:
        json.dump(data, f)

def saved_rgba(gc, dirpath):
    filename = gc.filename.split(os.sep)[-1].split('.')[0]
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    if gc.left_backwing is not None:
        cv2.imwrite(os.sep.join([dirpath, '{}_fore_left.png'.format(filename)]), gc.left_forewing)
    if gc.left_backwing is not None:
        cv2.imwrite(os.sep.join([dirpath, '{}_back_left.png'.format(filename)]), gc.left_backwing)
    if gc.right_forewing is not None:
        cv2.imwrite(os.sep.join([dirpath, '{}_fore_right.png'.format(filename)]), gc.right_forewing)
    if gc.right_backwing is not None:
        cv2.imwrite(os.sep.join([dirpath, '{}_back_right.png'.format(filename)]), gc.right_backwing)
    if gc.body is not None:
        cv2.imwrite(os.sep.join([dirpath, '{}_body.png'.format(filename)]), gc.body)

def main(args):
    '''
     - consider moth by parsing argument
     - load status by moth.STATE
     - update status by moth.STATE
     - consider moth by moth.ACTION
    '''
    template_path = 'image/10mm.png'
    metadata_path = 'metadata/'
    ext = ['jpg', 'jpeg', 'png']
    metadata_path = os.path.abspath(metadata_path)
    metadata_map = os.path.join(metadata_path, 'map.json')
    moths_path = os.path.abspath('image/sample')
    moths = [os.path.join(moths_path, moth) for moth in os.listdir(moths_path)]
    moths = [moth for moth in moths if moth.split('.')[-1] in ext]
    moths = sorted(moths)
    flatten = lambda l: [item for sublist in l for item in sublist]

    if args.image or args.recursive:
        moths = []
        if args.image: moths += [os.path.abspath(img) for img in args.image]
        if args.recursive:
            for repo in args.recursive:
                repo = [os.path.abspath(repo) + '/**/*.' + e for e in ext]
                repo = [glob.glob(r, recursive=True) for r in repo]
                repo = flatten(repo)
                moths += repo

    try:
        # checked file
        if not os.path.exists(metadata_path):
            os.makedirs(metadata_path)
        if not os.path.exists(metadata_map):
            with open(metadata_map, 'w') as f:
                json.dump({}, f)

        try:
            with open(metadata_map, 'r') as f:
                exist_data = json.load(f)
        except:
            exist_data = {}

        # core
        moth_index = 0
        next_index = 1
        _tmp_index = None
        navigation = False
        while True:
            if moth_index >= len(moths) or moth_index < 0: break
            moth = moths[moth_index]
            logging.info('({}/{}) Process {}'.format(
                moth_index+1, len(moths), moth.split(os.sep)[-1]))

            key = sha1(moth.encode('utf-8')).hexdigest()
            moth_path_split = moth.split(os.sep)
            moth_path_dir = os.sep.join(moth_path_split[:-1])
            moth_path_filename = moth_path_split[-1].split('.')[0]
            moth_path_metadata = os.path.join(moth_path_dir, moth_path_filename)
            key_json = os.path.join(moth_path_metadata, moth_path_filename + '.json')
            result = None

            # get history
            if key in exist_data.keys() and os.path.exists(key_json):

                is_done = (exist_data[key]['state'] == 'done')
                logging.info('  * STATE = {}'.format(exist_data[key]['state']))

                # check navigation
                if not navigation and not args.all and is_done and not args.image:
                    moth_index += next_index
                    if moth_index < 0 and _tmp_index is not None:
                        moth_index = _tmp_index
                        _tmp_index = None
                        navigation = True
                        next_index = 1
                        moth_index = max(moth_index, 0)
                    continue

                with open(key_json, 'r') as f:
                    last_status = json.load(f)
                    result = graph_cut(moth, template_path, last_status)

            if result is None: result = graph_cut(moth, template_path)

            with open(metadata_map, 'w') as f:
                exist_data.update({key: {'file': moth, 'state': result.STATE}})
                json.dump(exist_data, f, indent=4)

            # handling action
            if result.ACTION == 'save':
                saved_metadata(result, key_json)
                saved_rgba(result, moth_path_metadata)
                moth_index += 1
                if result.STATE == 'pause':
                    break
            elif result.ACTION == 'quit':
                break
            elif result.ACTION in ['nav_next', 'next']:
                if result.STATE == 'pause':
                    saved_metadata(result, key_json)
                if moth_index + 1 >= len(moths):
                    logging.warning('No more moth can be skipped')
                    continue
                navigation = True if result.ACTION == 'nav_next' else False
                next_index = 1
                moth_index += next_index
            elif result.ACTION in ['nav_previous', 'previous']:
                if result.STATE == 'pause':
                    saved_metadata(result, key_json)
                if moth_index - 1 < 0:
                    logging.warning('No more moth can be skipped')
                    continue
                navigation = True if result.ACTION == 'nav_previous' else False
                _tmp_index = moth_index
                next_index = -1
                moth_index += next_index
                moth_index = max(moth_index, 0)
            else:
                logging.warning('No specific action')
                moth_index += 1

    except Exception as e:
        logging.exception(e)

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )

    parser = argparser()
    main(parser.parse_args())
