"""
Support function for python profilling
"""

import time
import logging
from functools import wraps


LOGGER = logging.getLogger(__name__)

def func_profiling(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        time_spent = time.time() - start_time
        fullname = '{}.{}'.format(func.__module__, func.__name__)
        LOGGER.debug('{}[args={}, kwargs={}] completed in {}'.format(
            fullname, args, kwargs, time_spent
        ))
        return result
    return wrapped

@func_profiling
def test_func_profiling(sec):
    time.sleep(sec)

if __name__ == '__main__':
    """testing"""
    import sys
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(filename)12s:L%(lineno)3s [%(levelname)8s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )
    test_func_profiling(1)
