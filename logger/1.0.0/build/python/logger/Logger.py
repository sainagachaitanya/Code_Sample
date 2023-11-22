import logging
import sys
import os
from termcolor import colored

class ErrorFilter(logging.Filter):
    """
    Pass any message meant for stderr.
    """

    def __init__(self, *args, **kwargs):
        super(ErrorFilter, self).__init__(*args, **kwargs)

    # end __init__

    def filter(self, record):
        """
        If the record does is not logging.INFO, return True
        """
        return record.levelno != logging.INFO
    # end filter

class OutFilter(logging.Filter):
    """
    Pass any message meant for stderr.
    """

    def __init__(self, *args, **kwargs):
        super(OutFilter, self).__init__(*args, **kwargs)

    # end __init__

    def filter(self, record):
        """
        If the record does is logging.INFO, return True
        """
        return record.levelno == logging.INFO
    # end filter

class ColoredFormatter(logging.Formatter):
    def format(self, record):
            levelname = record.levelname
            msg = super().format(record)
            if levelname == 'DEBUG':
                return colored(msg, 'cyan')
            elif levelname == 'INFO':
                return colored(msg, 'green')
            elif levelname == 'WARNING':
                return colored(msg, 'yellow')
            elif levelname == 'ERROR':
                return colored(msg, 'red')
            elif levelname == 'CRITICAL':
                return colored(msg, 'red')
            return msg

class Logger:
    """
	Logger with stream redirection that can be extended based on the requirement

	Example:
		>>> class CustomLogger(Logger):
		>>>     LOGGER_NAME = "Custom Name"
        >>>     DEFAULT_LEVEL = logging.INFO
        >>>     FORMAT_DEFAULT = "[%(name)s][%(levelname)s] %(message)s"
        >>>     PROPAGATE_DEFAULT = True
        >>>     _logger_obj = None

        >>> Logger.debug("debug message")
        >>> Logger.info("info message")
        >>> Logger.warning("warning message")
        >>> Logger.error("error message")
        >>> Logger.critical("critical message")
        >>> Logger.log(25, "critical message")

        >>> try:
        >>>     a = []
        >>>     b = a[1]
        >>> except:
        >>>     Logger.exception("exception message")
        >>> Logger.set_level(logging.WARNING)
        >>> Logger.write_to_file("C:/Users/saichaitanya/Desktop/test.log")

            
	"""
    LOGGER_NAME = "Logger"
    DEFAULT_LEVEL = logging.DEBUG
    FORMAT_DEFAULT = "[%(name)s][%(levelname)s] %(message)s"
    PROPAGATE_DEFAULT = True
    _logger_obj = None

    @classmethod
    def logger_obj(cls):
        if not cls._logger_obj:
            if cls.logger_exists():
                cls._logger_obj = logging.getLogger(cls.LOGGER_NAME)
            else:
                cls._logger_obj = logging.getLogger(cls.LOGGER_NAME)
                cls._logger_obj.setLevel(cls.DEFAULT_LEVEL)
                cls._logger_obj.propagate = cls.PROPAGATE_DEFAULT

                basic_formatter = ColoredFormatter(cls.FORMAT_DEFAULT)

                # add stderr handling
                error = logging.StreamHandler(stream=sys.stderr)
                error.addFilter(ErrorFilter())
                error.setFormatter(basic_formatter)
                cls._logger_obj.addHandler(error)

                # add stdout handling
                out = logging.StreamHandler(stream=sys.stdout)
                out.addFilter(OutFilter())
                out.setFormatter(basic_formatter)
                cls._logger_obj.addHandler(out)

        return cls._logger_obj

    @classmethod
    def logger_exists(cls):
        return cls.LOGGER_NAME in logging.Logger.manager.loggerDict.keys()
    
    @classmethod
    def set_level(cls, level):
        lg = cls.logger_obj()
        lg.setLevel(level)

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.debug(msg, *args, **kwargs)
    
    @classmethod
    def info(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.info(msg, *args, **kwargs)
    
    @classmethod
    def warning(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.warning(msg, *args, **kwargs)
        
    @classmethod
    def error(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.error(msg, *args, **kwargs)
        
    @classmethod
    def critical(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.critical(msg, *args, **kwargs)
    
    @classmethod
    def log(cls, level, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.log(level, msg, *args, **kwargs)
    
    @classmethod
    def exception(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.exception(msg, *args, **kwargs)

    @classmethod
    def write_to_file(cls, path, level=logging.WARNING):
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(level)

        fmt = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
        file_handler.setFormatter(fmt)

        lg = cls.logger_obj()
        lg.addHandler(file_handler)

def main():
    Logger.set_level(logging.DEBUG)
    # Logger.write_to_file("C:/Users/saichaitanya/Desktop/test.log")
    Logger.debug("debug message")
    Logger.info("info message")
    Logger.warning("warning message")
    Logger.error("error message")
    Logger.critical("critical message")
    Logger.log(25, "critical message")
    
    try:
        a = []
        b = a[1]
    except:
        Logger.exception("exception message")
    
if __name__ == "__main__":
    main()