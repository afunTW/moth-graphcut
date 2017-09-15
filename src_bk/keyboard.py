import os

class KeyHandler(object):
    def __init__(self):
        super().__init__()
        if os.name == 'posix':
            self.KEY_LEFT = 81
            self.KEY_UP = 82
            self.KEY_RIGHT = 83
            self.KEY_DOWN = 84
            self.PAGEDOWN = 85
        elif os.name == 'nt':
            self.KEY_LEFT = 2424832
            self.KEY_UP = 2490368
            self.KEY_RIGHT = 2555904
            self.KEY_DOWN = 2621440
            self.PAGEDOWN = 2228224
            self.PAGEUP = 2162688