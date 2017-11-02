import logging
import os
import sys
sys.path.append('../..')

import cv2
from src.image.imnp import ImageNP
from src.support.tkconvert import TkConverter
from src.view.removal_app import RemovalViewer

LOGGER = logging.getLogger(__name__)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
