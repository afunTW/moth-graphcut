import os
import sys
import cv2
import pickle
import logging
import numpy as np

sys.path.append('.')
from src import grabcut
from scipy.ndimage.filters import gaussian_filter
from src import grabcut_tools


def grabcut_process(inGP, outimg):
    fore_pair = inGP.image_or(0, 1)
    back_pair = inGP.image_or(2, 3)
    moth_body = inGP.parts[-1].output
    track_image = inGP.track_image(0, 1, 2, 3, 4)
    fore_pair[fore_pair == [0]] = 255
    back_pair[back_pair == [0]] = 255
    moth_body[moth_body == [0]] = 255

    blur_mask = inGP.blur_image_or(255, 3, 0, 1, 2, 3)
    blur_body = inGP.orig_image.copy()
    blur_body[blur_mask == [255]] = 255
    blur_remain_body = blur_body.copy()

    # padding
    ix, iy, w, h = inGP.parts[-1].rect
    remain_body = inGP.remain_image(0, 1, 2, 3)
    remain_body[remain_body == [0]] = 255
    remain_wing = remain_body.copy()
    remain_wing[iy:iy+h, ix:ix+w] = 255
    fore_padding = fore_pair.copy()
    back_padding = back_pair.copy()

    for cover_index in range(4):
        ix, iy, w, h = inGP.parts[cover_index].rect
        tmp = remain_wing[iy:iy+h, ix:ix+w]
        base = fore_padding if cover_index in [0, 1] else back_padding
        base[iy:iy+h, ix:ix+w] = base[iy:iy+h, ix:ix+w] + tmp
        blur_remain_body[iy:iy+h, ix:ix+w] = 255

    cv2.imwrite(
        outimg,
        np.vstack((
            np.hstack((fore_pair, back_pair, moth_body)),
            np.hstack((fore_padding, back_padding, remain_body)),
            np.hstack((track_image, blur_body, blur_remain_body))
            ))
        )

def main():
    kmeans_path = os.path.abspath('./kmeans')
    kmeans_map = os.path.join(kmeans_path, 'cluster_map.p')

    with open(kmeans_map, 'rb') as f:
        cluster_map = pickle.load(f)
        logging.info('Load kmeans clustering map from %s' % kmeans_map)

    for i, cluster in cluster_map.items():

        saved_dir = os.path.abspath('/'.join(['.', 'result', str(i)]))
        if not os.path.exists(saved_dir):
            os.makedirs(saved_dir)
            logging.info('Create directory %s' % saved_dir)

        # interactive grabcut with center
        logging.info('grabcut %d cluster center %s' % (i, cluster['center']))
        center = grabcut_tools.GrabcutProcess(cluster['center'], iter_times=5)
        center.active()
        output = os.path.join(saved_dir, '_'.join(['cluster', str(i), 'center.png']))
        grabcut_process(center, output)

        # grabcut neighbor by center parameters
        for j, img in enumerate(cluster['neighbor']):
            logging.info(
                'grabcut %d cluster neighbor (%d/%d) %s' %
                (i, j, len(cluster['neighbor']), img))

            neighbor = grabcut_tools.GrabcutProcess(img, iter_times=5)
            neighbor.rect = [_.rect for _ in center.parts]
            neighbor.mask_records = [_.mask_records for _ in center.parts]
            neighbor.segment_count = [_.segment_count for _ in center.parts]
            neighbor.simulate()
            output = os.path.join(
                saved_dir,
                ''.join(['cluster_', str(i), '_neighbor_', str(j), '.png'])
                )
            grabcut_process(neighbor, output)

if __name__ == '__main__':

    # print documentation
    print(__doc__)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [ %(levelname)8s ] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )

    main()
