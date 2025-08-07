"""
Универсальный модуль логирования для всех компонентов WebKurierDrone.
"""

import logging
import os

def setup_logger(name="webkurier", log_file="logs/webkurier.log", level=logging.INFO):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler = logging.FileHandler(log_file, encoding='utf-8')        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger

# Пример:
if __name__ == "__main__":
    log = setup_logger()
    log.info("Система логирования инициализирована.")
