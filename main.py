import os
import sys
import cv2
import pickle
import logging
import numpy as np

sys.path.append('.')
from src import grabcut
from scipy.ndimage.filters import gaussian_filter


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
        center = []
        for iter_times in range(5):
            part = grabcut.Grabcut(cluster['center'])
            part.active()
            center.append(part)

        fore_pair = np.bitwise_or(center[0].output, center[1].output)
        back_pair = np.bitwise_or(center[2].output, center[3].output)
        wing_mask = np.bitwise_or(fore_pair, back_pair)
        moth_body = center[4].output

        blur_mask = gaussian_filter(wing_mask, sigma=3)
        blur_mask = cv2.cvtColor(blur_mask, cv2.COLOR_BGR2GRAY)
        blur_mask[np.where(blur_mask != 0)] = 255
        blur_mask = cv2.cvtColor(blur_mask, cv2.COLOR_GRAY2BGR)

        fore_pair[fore_pair == [0]] = 255
        back_pair[back_pair == [0]] = 255
        moth_body[moth_body == [0]] = 255
        remain_body = np.bitwise_xor(center[0].orig_image, wing_mask)
        # remain_body[remain_body == [0]] = 255
        blur_body = center[0].orig_image.copy()
        blur_body[blur_mask == [255]] = 255

        # test
        ix, iy, w, h = center[4].rect
        remain_body[iy:iy+h, ix:ix+w] = 0

        for cover_index in range(4):
            ix, iy, w, h = center[cover_index].rect
            tmp = remain_body[iy:iy+h, ix:ix+w]
            base = fore_pair if cover_index in [0, 1] else back_pair
            base[iy:iy+h, ix:ix+w] = base[iy:iy+h, ix:ix+w] + tmp

        remain_body[remain_body == [0]] = 255

        cv2.imwrite(
            os.path.join(saved_dir, '_'.join(['cluster', str(i), 'center.png'])),
            np.vstack((
                np.hstack((fore_pair, back_pair, center[4].output)),
                np.hstack((center[0].orig_image, remain_body, blur_body))
                ))
            )

        # grabcut neighbor by center parameters
        for j, img in enumerate(cluster['neighbor']):
            logging.info('grabcut %d cluster neighbor (%d/%d) %s' % (i, j, len(cluster['neighbor']), img))
            neighbor = []
            for iter_times in range(5):
                part = grabcut.Grabcut(img)
                part.rect = center[iter_times].rect
                part.mask_records = center[iter_times].mask_records
                part.segment_count = center[iter_times].segment_count
                part.simulate()
                neighbor.append(part)

            fore_pair = np.bitwise_or(neighbor[0].output, neighbor[1].output)
            back_pair = np.bitwise_or(neighbor[2].output, neighbor[3].output)
            wing_mask = np.bitwise_or(fore_pair, back_pair)
            moth_body = neighbor[4].output

            blur_mask = gaussian_filter(wing_mask, sigma=3)
            blur_mask = cv2.cvtColor(blur_mask, cv2.COLOR_BGR2GRAY)
            blur_mask[np.where(blur_mask != 0)] = 255
            blur_mask = cv2.cvtColor(blur_mask, cv2.COLOR_GRAY2BGR)

            fore_pair[fore_pair == [0]] = 255
            back_pair[back_pair == [0]] = 255
            moth_body[moth_body == [0]] = 255
            remain_body = np.bitwise_xor(neighbor[0].orig_image, wing_mask)
            remain_body[remain_body == [0]] = 255
            blur_body = neighbor[0].orig_image.copy()
            blur_body[blur_mask == [255]] = 255

            # test
            test = neighbor[0].orig_image
            for _ in range(5):
                x, y, w, h = neighbor[_].rect
                cv2.rectangle(test, (x, y), (x + w, y + h), [255, 0, 0], 2)
                for tmp in neighbor[_].mask_records:
                    cv2.circle(test, tmp['coordinate'], 3, tmp['value']['color'], -1)
                    cv2.circle(test, tmp['coordinate'], 3, tmp['value']['val'], -1)

            cv2.imwrite(
                os.path.join(
                    saved_dir,
                    ''.join(['cluster_', str(i), '_neighbor_', str(j), '.png'])
                ),
                np.vstack((
                    np.hstack((fore_pair, back_pair, neighbor[4].output)),
                    np.hstack((test, remain_body, blur_body))
                    ))
                )

        # test
        break

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
