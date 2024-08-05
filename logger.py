import logging
from logging.handlers import RotatingFileHandler
import os
from config import ENABLE_LOGGING, LOG_FILE,DEBUG

def setup_logger(name = "proxy_server"):
    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG if DEBUG else logging.info)

    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    if ENABLE_LOGGING:
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1048576, backupCount=5)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()