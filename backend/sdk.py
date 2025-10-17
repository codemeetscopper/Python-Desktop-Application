import time

from common.data import AppData
from common.logger import Logger


class SDK:
    def initialise(self):
        logger = Logger()
        for x in range(0, 110, 10):
            AppData().set_progress(value=x, message=f"({x}%)  Initialising backend...")
            time.sleep(0.5)
        # raise Exception("backend init error 101")
        return True
