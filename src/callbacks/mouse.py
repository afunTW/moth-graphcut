"""
Defined callback functions of mouse event
"""
import logging
import sys
sys.path.append('../')

from support.profiling import func_profiling

LOGGER = logging.getLogger(__name__)

@func_profiling
def draw_circle(e, w, color='#000000'):
    """default draw with balck color"""
    x1, y1 = (e.x-1), (e.y-1)
    x2, y2 = (e.x+1), (e.y+1)
    w.create_oval(x1, y1, x2, y2, fill=color)
