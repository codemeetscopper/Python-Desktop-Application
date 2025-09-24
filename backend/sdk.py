import time

from common.logger import Logger


class SDK:
    def initialise(self):
        logger = Logger()
        for x in range(10):
            logger.debug(f"backend init {x}..")
            time.sleep(1)
        return True