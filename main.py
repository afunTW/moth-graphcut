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
        blur_mask = gaussian_filter(wing_mask, sigma=3)
        blur_mask = cv2.cvtColor(blur_mask, cv2.COLOR_BGR2GRAY)
        blur_mask[np.where(blur_mask != 0)] = 255
        blur_mask = cv2.cvtColor(blur_mask, cv2.COLOR_GRAY2BGR)
        remain_body = np.bitwise_xor(center[0].orig_image, wing_mask)
        blur_body = np.bitwise_xor(center[0].orig_image, blur_mask)

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
            blur_mask = gaussian_filter(wing_mask, sigma=3)
            blur_mask = cv2.cvtColor(blur_mask, cv2.COLOR_BGR2GRAY)
            blur_mask[np.where(blur_mask != 0)] = 255
            blur_mask = cv2.cvtColor(blur_mask, cv2.COLOR_GRAY2BGR)
            remain_body = np.bitwise_xor(neighbor[0].orig_image, wing_mask)
            blur_body = neighbor[0].orig_image.copy()

            for row in range(neighbor[0].orig_image.shape[1]):
                for column in range(neighbor[0].orig_image.shape[0]):
                    if blur_mask[row, column] == 255:
                        blur_body[row, column] = 0

            # test
            test = neighbor[0].orig_image
            for _ in range(5):
                cv2.rectangle(test, neighbor[_].rect[0:1], neighbor[_].rect[2:], [255, 0, 0])
                for tmp in neighbor[_].mask_records:
                    cv2.circle(test, tmp['corrdinate'], 3, tmp['value']['color'], -1)
                    cv2.circle(test, tmp['corrdinate'], 3, tmp['value']['val'], -1)

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
