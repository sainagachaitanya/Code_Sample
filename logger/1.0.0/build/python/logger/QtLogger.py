from PySide2 import QtCore as Qtc
import logging
from .Logger import Logger

class QtSignaler(Qtc.QObject):
    message_logged = Qtc.Signal(str)

class QtSignalHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(QtSignalHandler, self).__init__(*args, **kwargs)
        self.emitter = QtSignaler()

    def emit(self, record):
        msg = self.format(record)
        self.emitter.message_logged.emit(msg)


class QtLogger(Logger):
    _signal_handler = None

    @classmethod
    def logger_obj(cls):
        pass

    @classmethod
    def signal_handler(cls):
        cls.logger_obj()