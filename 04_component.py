import glob
import json
import logging
import os
import sys
from inspect import currentframe, getframeinfo

import numpy as np

from src.actions.component_app import EntryThermalComponentAction

__FILE__ = os.path.abspath(getframeinfo(currentframe()).filename)
LOGGER = logging.getLogger(__name__)


def main():
    entry = EntryThermalComponentAction()
    entry.mainloop()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    main()
