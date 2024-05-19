import logging
from logging.handlers import RotatingFileHandler


class BotLogger:
    def __init__(self, log_file, encoding='utf-8'):
        self.logger = logging.getLogger("bot_logger")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        with open(log_file, 'a', encoding=encoding) as file:
            file_handler = RotatingFileHandler(log_file, maxBytes=1024000, backupCount=5, encoding=encoding)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_info(self, message):
        self.logger.info(message)

    def log_error(self, message):
        self.logger.error(message)
