import time

from common.logger import Logger


class SDK:
    def initialise(self):
        logger = Logger()
        for x in range(5):
            logger.debug(f"backend init {x}..")
            time.sleep(0.5)
        # raise Exception("backend init error 101")
        return True