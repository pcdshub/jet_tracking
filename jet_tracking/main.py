import ctypes
import sys, os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.Qt import Qt
#from . import datastream
#sys.path.append('/reg/g/pcds/epics-dev/ajshack/jet_tracking/jet_tracking')
from gui.windows.mainWindow import MainWindow
import logging

log = logging.getLogger(__name__)

class App(QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)
        log.debug("This is the mainThread")
        self.init_logging()
        self.setAttribute(Qt.AA_EnableHighDpiScaling)
        self.setStyle("Fusion")
        self.mainWindow = MainWindow()
        self.mainWindow.setWindowTitle("jet-tracker")
        self.mainWindow.show()

    @staticmethod
    def init_logging():
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)

        # Console Handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s\t (%(name)-25.25s) (thread:%(thread)d) (line:%(lineno)5d)\t[%(levelname)-5.5s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
def main():
    # Makes the icon in the taskbar as well.
    appID = "opt-id"  # arbitrary string
    if os.name == 'nt':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID)
    elif os.name == 'posix':
        pass

    app = App(sys.argv)
    # app.setWindowIcon(QIcon(application_path + "{0}gui{0}misc{0}logo{0}logo3.ico".format(os.sep)))
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
