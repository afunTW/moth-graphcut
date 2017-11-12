import logging
import sys
from glob import glob
from inspect import currentframe, getframeinfo
from os import path

from src.actions.graphcut_app import GraphCutAction

__FILE__ = path.abspath(getframeinfo(currentframe()).filename)

LOGGER = logging.getLogger(__FILE__)


def main():
    graphcut_action = GraphCutAction()
    graphcut_action.input_images()
    graphcut_action.mainloop()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    main()
