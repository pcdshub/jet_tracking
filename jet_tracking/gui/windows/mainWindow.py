import logging
import sys

from context import Context
from gui.views.jetImageView import JetImageView
from gui.views.jetTrackerView import JetTrackerView
from gui.windows.mainWindowUi import Ui_MainWindow
from gui.windows.simulationWindow import SimWindow
from PyQt5.Qt import Qt
from PyQt5.QtCore import QCoreApplication, QSize
from PyQt5.QtWidgets import (QAction, QLabel, QMainWindow, QSizePolicy,
                             QTabWidget)
from signals import Signals

log = logging.getLogger("jet_tracker")


try:
    from ...pyqt_stylesheets import pyqtcss  # noqa: E402  # isort: skip
except ImportError:
    pyqtcss = None
    log.exception(
        "Failed to import pyqt-stylesheets. "
        "Did you not clone recursively?"
    )


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    This class represents the main window of the GUI application and inherits from both
    QMainWindow and Ui_MainWindow classes.

    """
    def __init__(self):
        """
        Constructor method for the MainWindow class.
        Initializes the main window and sets its attributes.
        Sets the size and style sheet for the main window.
        Creates instances of other views and dialogs.
        Sets up the window tabs.
        Creates the menu bar actions.
        Connects buttons and signals.

        Args:
            signals (class): creates the instance of the signals class which every
            widget in the application receives so that signals can be shared among classes
            context (class): creates the instance of the context class which every
            widget in the application receives so that when values are updated, it changes in all
            locations and everyone gets the same information.
            simWindow (class): the simulation window for changing simulation parameters. It can be opened
            in the menu bar under tools
            tabWidget (class): sets up the different tab views
            jetTrackerView (class): connects the first tab view to the main window
            jetImageView (class): connects the second tab view to the main window
        """
        super().__init__()
        log.debug("Supplying Thread information from init of MainWindow.")
        self.setAttribute(Qt.WA_AlwaysStackOnTop)
        self.setMinimumSize(QSize(700, 300))
        self.resize(QSize(1800, 1100))
        if pyqtcss is not None:
            self.setStyleSheet(pyqtcss.get_style("dark_orange"))
        else:
            log.info("Optional dependency pyqtcss is unavailable")

        self.signals = Signals()
        self.context = Context(self.signals)
        self.setupUi(self)
        self.simWindow = None
        self.tabWidget = None
        self.jetTrackerView = None
        self.jetImageView = None
        self.create_views_and_dialogs()
        self.setup_window_tabs()
        self.createMenuBarActions()
        self.connect_buttons()
        self.connect_signals()

    def setup_window_tabs(self):
        """Sets up the window tabs in the main window."""
        self.setDockNestingEnabled(True)
        self.tabWidget = QTabWidget()
        self.tabWidget.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Expanding)
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.addTab(self.jetTrackerView, "Jet Tracker")
        self.tabWidget.addTab(self.jetImageView, "Jet Image")

    def create_views_and_dialogs(self):
        """Creates instances of different views and dialogs used in the application."""
        self.simWindow = SimWindow(self.context, self.signals)
        self.jetTrackerView = JetTrackerView(self.context, self.signals, self)
        self.jetImageView = JetImageView(self.context, self.signals)
        # self.helpDialog = HelpDialog()

    def createFileActions(self):
        """Creates actions for the File menu."""
        ids = ["Open", "Export", "Exit"]
        tips = ["open exported file to run in simulation mode",
                "export all or some data",
                "exit the application"]
        shortcuts = ['Ctrl+O', 'Ctrl+Shift+E', 'Ctrl+Q']
        connects = [self.openFile, self.exportData, self.close]
        L = []
        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.setStatusTip(tips[i])
            a.triggered.connect(self.restoreFocus)
            if connects[i] != 0:
                a.triggered.connect(connects[i])
            L.append(a)

        L.insert(3, 0)
        return L

    def createEditActions(self):
        """Creates actions for the Edit menu."""
        ids = ["undo", "redo"]
        shortcuts = ['Ctrl+Z', 'Ctrl+Y']
        connects = [self.undo, self.redo]
        tips = ["undo last action", "redo last action"]
        L = []
        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.setStatusTip(tips[i])
            a.triggered.connect(self.restoreFocus)
            if connects[i] != 0:
                a.triggered.connect(connects[i])
            L.append(a)

        L.insert(2, 0)
        return L

    def createHelpActions(self):
        """Creates actions for the Help menu."""
        ids = ["contents", "about"]
        shortcuts = ['F1', 'Ctrl+B']
        connects = [self.showHelp, self.showAboutDialog]
        L = []
        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.triggered.connect(self.restoreFocus)
            if connects[i] != 0:
                a.triggered.connect(connects[i])
            L.append(a)

        L.insert(1, 0)
        return L

    def createToolActions(self):
        """Creates actions for the Tool menu."""
        ids = ["Simulation Toolbar", "Image Processing Toolbar"]
        shortcuts = ['F5', 'F7']
        connects = [self.showSimToolbar, self.showImageToolbar]
        L = []
        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.triggered.connect(self.restoreFocus)
            if connects[i] != 0:
                a.triggered.connect(connects[i])
            L.append(a)

        L.insert(1, 0)
        return L

    def createMenuBarActions(self):
        """Creates the menu bar actions by calling the respective create*Actions
        functions and adds them to the appropriate menus."""
        self.fileActions = self.createFileActions()
        self.editActions = self.createEditActions()
        self.helpActions = self.createHelpActions()
        self.toolActions = self.createToolActions()
        for i in self.fileActions:
            if i == 0:
                self.fileMenu.addSeparator()
            else:
                self.fileMenu.addAction(i)
        for i in self.editActions:
            if i == 0:
                self.editMenu.addSeparator()
            else:
                self.editMenu.addAction(i)
        for i in self.helpActions:
            if i == 0:
                self.helpMenu.addSeparator()
            else:
                self.helpMenu.addAction(i)
        for i in self.toolActions:
            if i == 0:
                self.toolMenu.addSeparator()
            else:
                self.toolMenu.addAction(i)

    def restoreFocus(self):
        """Restores the focus of the main window and clears any pressed keys or mouse actions."""
        log.info("Restoring Focus")
        self.ctrlPressed = False
        self.releaseMouse()
        self.releaseKeyboard()
        QCoreApplication.instance().restoreOverrideCursor()

    def connect_buttons(self):
        pass
        # self.helpAction.triggered.connect(self.show_helpDialog)

    def connect_signals(self):
        pass
        # self.helpDialog.s_windowClose.connect(lambda: self.setEnabled(True))

    def setup_statusBar(self):
        """Sets up the status bar in the main window."""
        self.statusbarMessage = QLabel()
        self.statusbar.addWidget(self.statusbarMessage)

    def show_helpDialog(self):
        """Shows the help dialog when the Help action is triggered."""
        log.info('Help Dialog Opened')
        self.setEnabled(False)
        self.helpDialog.exec_()

    def openFile(self):  # Unused, needs to be removed elsewhere
        print("open file")

    def exportData(self):
        print("you tried to export data")

    def closeEvent(self, event):
        self.signals.terminateAll.emit()
        event.accept()

    def undo(self):  # Possible future addition
        print("undo")
        # if self.context.currentImage().posHistory > 0:
        #     self.context.currentImage().posHistory -= 1
        #     self.context.currentImage().image = QtWidgets.QImage(
        #         self.context.currentImage().history[
        #             self.context.currentImage().posHistory])
        #     self.signals.updateCanvas.emit()
        #     self.signals.resizeCanvas.emit()

    def redo(self):  # Possible future addition
        print("redo")
        # if (self.context.currentImage().posHistory <
        #         len(self.context.currentImage().history) - 1):
        #     self.context.currentImage().posHistory += 1
        #     self.context.currentImage().image = QtWidgets.QImage(
        #         self.context.currentImage().history[
        #             self.context.currentImage().posHistory])
        #     self.signals.updateCanvas.emit()
        #     self.signals.resizeCanvas.emit()

    def showHelp(self):
        pass

    def showAboutDialog(self):
        pass

    def showSimToolbar(self):
        self.simWindow.show()

    def showImageToolbar(self):
        log.info("Image toolbar")
