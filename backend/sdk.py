import time

from common.data import AppData
from common.logger import Logger


class SDK:
    def initialise(self):
        logger = Logger()
        for x in range(0, 100, 10):
            AppData().set_progress(value=x, message=f"({x}%)  Initialising backend...")
            time.sleep(0.2)
        # raise Exception("backend init error 101")
        return True
