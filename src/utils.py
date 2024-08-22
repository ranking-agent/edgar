import logging
import json
import os
import yaml
from collections import namedtuple
import copy
from logging.handlers import RotatingFileHandler
from datetime import datetime


class LoggingUtil(object):
    """ Logging utility controlling format and setting initial logging level """

    @staticmethod
    def init_logging(name, level=logging.INFO, format='short', logFilePath=None, logFileLevel=None):
        # Check if the logger already exists
        logger = logging.getLogger(name)
        if logger.hasHandlers():
            # Avoid adding handlers again if they already exist
            return logger

        FORMAT = {
            "short": '%(funcName)s: %(message)s',
            "medium": '%(funcName)s: %(asctime)-15s %(message)s',
            "long": '%(asctime)-15s %(filename)s %(funcName)s %(levelname)s: %(message)s'
        }[format]

        # create a stream handler (default to console)
        stream_handler = logging.StreamHandler()

        # create a formatter
        formatter = logging.Formatter(FORMAT)

        # set the formatter on the console stream
        stream_handler.setFormatter(formatter)

        # set the logging level
        logger.setLevel(level)

        # if there was a file path passed in, use it
        if logFilePath is not None:
            # create a rotating file handler, 100mb max per file with a max number of 10 files
            file_handler = RotatingFileHandler(filename=os.path.join(logFilePath, f'{name}.log'), maxBytes=1000000, backupCount=10)

            # set the formatter
            file_handler.setFormatter(formatter)

            # if a log level for the file was passed in, use it
            if logFileLevel is not None:
                file_handler.setLevel(logFileLevel)
            else:
                file_handler.setLevel(level)

            # add the file handler to the logger
            logger.addHandler(file_handler)

        # add the console handler to the logger
        logger.addHandler(stream_handler)

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

        # return to the caller
        return logger


def create_log_entry( msg: str, err_level, code=None ) -> dict:
    now = datetime.now()

    # load the data
    ret_val = {
        'timestamp': now.strftime("%m-%d-%Y %H:%M:%S"),
        'level': err_level,
        'message': msg,
        'code': code
    }

    # return to the caller
    return ret_val