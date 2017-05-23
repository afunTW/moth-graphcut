import os
import sys
import cv2
import json
import logging
import numpy as np

from hashlib import sha1
from src import detector
from src import graphic


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

def main(filename, template=None, last_status=None):

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
    gb = graphic.GraphCut(filename, orig_image=orig_image)
    logging.info(' Process graph cut')

    if last_status:
        logging.info(' Rollback to last status')

        if last_status['mirror_line']:
            pt1 , pt2 = last_status['mirror_line']
            gb.mirror_line = (tuple(pt1), tuple(pt2))

        if last_status['mirror_shift']:
            gb.mirror_shift = last_status['mirror_shift']

        if any([v for v in last_status['tracking_label']]):
            gb.tracking_label = last_status['tracking_label']

    gb.run()

    return gb

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [ %(levelname)8s ] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )

    try:
        template_path = 'image/10mm.png'
        metadata_path = 'metadata/'
        metadata_path = os.path.abspath(metadata_path)
        metadata_map = os.path.join(metadata_path, 'map.json')
        moths_path = os.path.abspath('image/sample')
        moths = [os.path.join(moths_path, moth) for moth in os.listdir(moths_path)]

        if not os.path.exists(metadata_path):
            os.makedirs(metadata_path)

        if not os.path.exists(metadata_map):
            with open(metadata_map, 'w') as f:
                json.dump({}, f)

        with open(metadata_map, 'r') as f:
            exist_data = json.load(f)

        for i, moth in enumerate(moths):
            logging.info('({}/{}) Process {}'.format(
                i+1, len(moths), moth.split('/')[-1]))

            key = sha1(moth.encode('utf-8')).hexdigest()
            key_json = ''.join([key, '.json'])
            key_json = os.path.join(metadata_path, key_json)

            if key in exist_data.keys() and os.path.exists(key_json):
                with open(key_json, 'r') as f:
                    last_status = json.load(f)
                result = main(moth, template=template_path, last_status=last_status)
            else:
                result = main(moth, template=template_path)
                with open(metadata_map, 'w') as f:
                    exist_data.update({key: moth})
                    json.dump(exist_data, f, indent=4)

            data = {
                'name': moth,
                'state': result.STATE,
                'mirror_line': result.mirror_line,
                'mirror_shift': result.mirror_shift,
                'tracking_label': result.tracking_label,
                'components_color': all_to_list(result.components_color.copy()),
                'components_contour': all_to_list(result.components_contour.copy())
            }

            with open(key_json, 'w+') as f:
                json.dump(data, f)

            # break

    except Exception as e:
        logging.exception(e)
