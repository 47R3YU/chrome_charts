""" Module containing helper functions for timestamp conversion and logging """

# standard libs
import sys
import datetime
import logging
from logging.handlers import RotatingFileHandler
# app modules
from core import config


def date_from_webkit(timestamp):
    """ Convert webkit timestamp format (used by chrome history) to YY-MM-DD string """
    epoch_start = datetime.datetime(1601, 1, 1)
    delta = datetime.timedelta(microseconds=int(timestamp))
    date_ = epoch_start + delta
    return date_.strftime("%Y-%m-%d")


def date_to_webkit(date_string):
    """ Convert YY-MM-DD string to webkit timestamp """
    epoch_start = datetime.datetime(1601, 1, 1)
    date_ = datetime.datetime.strptime(date_string, "%Y-%m-%d")
    diff = date_ - epoch_start
    seconds_in_day = 60 * 60 * 24
    return '{:<017d}'.format(diff.days * seconds_in_day + diff.seconds + diff.microseconds)


def get_logger(path=config.LOG_FILE, max_size=512, printing=config.PRINT_LOG, log_level=config.LOG_LEVEL):
    """ Returns a logging object initiated with the config params """

    custom_logger = logging.getLogger("Rotating Log")
    custom_logger.setLevel(logging.DEBUG)

    if log_level != "DEBUG":
        log_level = log_level.upper()
        if log_level == "CRITICAL":
            custom_logger.setLevel(logging.CRITICAL)
        elif log_level == "WARNING":
            custom_logger.setLevel(logging.WARNING)
        elif log_level == "INFO":
            custom_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt="{asctime} [{levelname:<5}][{filename}@{lineno:03}] {message}", datefmt="%Y-%m-%d %H:%M:%S", style="{")

    # clean up handlers
    if custom_logger.handlers:
        for handler in custom_logger.handlers.copy():
            custom_logger.removeHandler(handler)

    handler = RotatingFileHandler(path, maxBytes=max_size, backupCount=0)
    handler.setFormatter(formatter)
    custom_logger.addHandler(handler)

    # print log-messages to console if printing is True
    if printing:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        custom_logger.addHandler(console_handler)

    return custom_logger


def close_logger():
    """ Helper to shut down logging properly """
    logging.shutdown()
