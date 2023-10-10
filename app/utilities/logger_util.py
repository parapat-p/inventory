import os

from datetime import datetime
from loguru import logger

class LoggerUtil(object):
    def __init__(self) -> None:
        super().__init__()
        self.init_logger() 

    def init_logger(self):
        stamp_today = datetime.now()
        today = stamp_today.strftime("%Y%m%d")
        path_log = os.path.join(".", "app", "log", "{}.log".format(today))
        logger.add(path_log, encoding='utf-8', enqueue=True, diagnose=True)
        logger.debug(path_log)