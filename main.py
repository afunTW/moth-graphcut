import pickle
import logging
import numpy as np
import cv2
import sys
import os

sys.path.append('.')
from src import superpixel
from skimage.segmentation import slic
from skimage.segmentation import felzenszwalb
from skimage.segmentation import quickshift
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float

def main():
    kmeans_path = os.path.abspath('./kmeans')
    kmeans_map = os.path.join(kmeans_path, 'shape_map.p')

    with open(kmeans_map, 'rb') as f:
        cluster_map = pickle.load(f)
        logging.info('Load kmeans clustering map from %s' % kmeans_map)

    for i, cluster in cluster_map.items():

        saved_dir = os.path.abspath('/'.join(['.', 'result', str(i)]))
        output = os.path.join(saved_dir, '_'.join(['cluster', str(i), 'center.png']))
        if not os.path.exists(saved_dir):
            os.makedirs(saved_dir)
            logging.info('Create directory %s' % saved_dir)

        logging.info(
            'cluster (%d/%d) center %s' %
            (i+1, len(cluster_map), cluster['center']))

        # test
        center = superpixel.SuperPixel(cluster['center'])
        center.segment = slic(img_as_float(center.orig_image), n_segments=2000, sigma=0.1)
        # center.segment = felzenszwalb(img_as_float(center.orig_image), scale=100, sigma=0.5)
        center.active()
        cv2.imwrite(output, np.hstack((center.image, center.output)))
        logging.info('Save in %s' % output)

        # for j, img in enumerate(cluster['neighbor']):
        #     logging.info(
        #         'cluster (%d/%d) neighbor (%d/%d) %s' %
        #         (i+1, len(cluster_map), j+1, len(cluster['neighbor']), img))

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
