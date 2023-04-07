import ctypes
import logging
import os
import sys

from gui.windows.mainWindow import MainWindow
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread

"""handler = logging.StreamHandler()
handler.setLevel(logging.CRITICAL)
formatter = logging.Formatter(
            "%(asctime)s\t (%(name)-25.25s) (thread:%(thread)d) "
            "(line:%(lineno)5d)\t[%(levelname)-5.5s] %(message)s")
handler.setFormatter(formatter)
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("jet_tracker")
log.setLevel('DEBUG')
log.addHandler(handler)"""

# create logger
log = logging.getLogger('jet_tracker')
log.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(thread)d - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
log.addHandler(ch)


class App(QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)
        #self.init_logging()
        log.debug("Supplying Thread information from init of QApplication")
        self.setAttribute(Qt.AA_EnableHighDpiScaling)
        self.setStyle("Fusion")
        self.mainWindow = MainWindow()
        self.mainWindow.setWindowTitle("jet-tracker")
        self.mainWindow.show()

    @staticmethod
    def init_logging():
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Console Handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.CRITICAL)
        formatter = logging.Formatter(
            "%(asctime)s\t (%(name)-25.25s) (thread:%(thread)d) "
            "(line:%(lineno)5d)\t[%(levelname)-5.5s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        log.error("Uncaught exception", exc_info=(exc_type, exc_value,
                                                  exc_traceback))


def main():
    # Makes the icon in the taskbar as well.
    appID = "opt-id"  # arbitrary string
    if os.name == 'nt':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID)
    elif os.name == 'posix':
        pass

    app = App(sys.argv)
    # To add icon:
    # app.setWindowIcon(QIcon(application_path
    #                   + "{0}gui{0}misc{0}logo{0}logo3.ico".format(os.sep)))
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
