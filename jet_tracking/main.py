import ctypes
import logging
import os
import sys

from gui.windows.mainWindow import MainWindow
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QApplication

# Append stylesheet path
sys.path.append('/cds/group/pcds/epics-dev/ajshack/jet_tracking/jet_tracking/pyqt-stylesheets/')

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
    # This class represents the main application instance and inherits from QApplication class of PyQt.
    # It initializes the application, sets up logging, and creates the main window for the GUI.
    def __init__(self, sys_argv):
        """

        Constructor method for the App class.

        Parameters:
            sys_argv(list): Command - line arguments passed to the application.

        """
        super().__init__(sys_argv)
        log.debug("Supplying Thread information from init of QApplication")
        self.setAttribute(Qt.AA_EnableHighDpiScaling)
        self.setStyle("Fusion")
        self.mainWindow = MainWindow()
        self.mainWindow.setWindowTitle("jet-tracker")
        #__location__ = os.getcwd()
        #File = open(__location__ + '\jt_configs\Geoo.qss', 'r')
        #with File:
        #    qss = File.read()
        #    self.setStyleSheet(qss)
        self.mainWindow.show()

    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Static method for handling uncaught exceptions.

        Parameters:
            exc_type(type): Type of the exception.
            exc_value(Exception): The exception instance.
            exc_traceback(traceback): The traceback object.

        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        log.error("Uncaught exception", exc_info=(exc_type, exc_value,
                                                  exc_traceback))


def main():
    """

    The main function that starts the application and executes the event loop.

    """
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
