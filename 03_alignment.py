import logging
import os
import sys

from src.actions.mapping_app import EntryMappingAction

LOGGER = logging.getLogger(__name__)

def main():
    alignment_entry = EntryMappingAction()
    alignment_entry.mainloop()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    main()