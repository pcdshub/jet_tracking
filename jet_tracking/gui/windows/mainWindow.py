from PyQt5.Qt import Qt
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QTabWidget, QAction, QMainWindow, QLabel, QSizePolicy
from context import Context
from gui.views.jetTrackerView import JetTrackerView
from gui.views.jetImageView import JetImageView
from gui.windows.mainWindowUi import Ui_MainWindow
from signals import Signals
from gui.windows.simulationWindow import SimWindow
import logging

log = logging.getLogger(__name__)


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setAttribute(Qt.WA_AlwaysStackOnTop)
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
        self.setDockNestingEnabled(True)
        self.tabWidget = QTabWidget()
        self.tabWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.addTab(self.jetTrackerView, "Jet Tracker")
        self.tabWidget.addTab(self.jetImageView, "Jet Image")

    def create_views_and_dialogs(self):
        self.simWindow = SimWindow(self.context, self.signals)
        self.jetTrackerView = JetTrackerView(self.context, self.signals, self)
        self.jetImageView = JetImageView(self.context, self.signals)
        # self.helpDialog = HelpDialog()

    def createFileActions(self):
        ids = ["Open", "Export", "Exit"]
        tips = ["open exported file to run in simulation mode", "export all or some data",
                " exit the application"]
        shortcuts = ['Ctrl+O', 'Ctrl+Shift+E', 'Ctrl+Q']
        connects = [self.openFile, self.exportData, self.close]
        L = []
        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.setStatusTip(tips[i])
            a.triggered.connect(self.restoreFocus)
            if connects[i] != 0: a.triggered.connect(connects[i])
            L.append(a)

        L.insert(3, 0)
        return L

    def createEditActions(self):
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
            if connects[i] != 0: a.triggered.connect(connects[i])
            L.append(a)

        L.insert(2, 0)
        return L

    def createHelpActions(self):
        ids = ["contents", "about"]
        shortcuts = ['F1', 'Ctrl+B']
        connects = [self.showHelp, self.showAboutDialog]
        L = []
        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.triggered.connect(self.restoreFocus)
            if connects[i] != 0: a.triggered.connect(connects[i])
            L.append(a)

        L.insert(1, 0)
        return L

    def createToolActions(self):
        ids = ["Simulation Toolbar", "Image Processing Toolbar"]
        shortcuts = ['F5', 'F7']
        connects = [self.showSimToolbar, self.showImageToolbar]
        L = []
        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.triggered.connect(self.restoreFocus)
            if connects[i] != 0: a.triggered.connect(connects[i])
            L.append(a)

        L.insert(1, 0)
        return L

    def createMenuBarActions(self):
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
        #self.helpDialog.s_windowClose.connect(lambda: self.setEnabled(True))

    def setup_statusBar(self):
        self.statusbarMessage = QLabel()
        self.statusbar.addWidget(self.statusbarMessage)

    def show_helpDialog(self):
        log.info('Help Dialog Opened')
        self.setEnabled(False)
        self.helpDialog.exec_()

    def openFile(self):
        print("open file")
        #fileName = QtWidgets.QFileDialog.getOpenFileName(self,
        #            self.context.getText("dialog_open", "title"),
        #            "/home",
        #            self.context.getText("dialog_open", "images") + u" (*.bmp *.gif *.png *.xpm *.jpg);;" + self.context.getText("dialog_open", "all_files") + u" (*)")
        #if fileName:
        #    self.context.loadImage(fileName)

    def exportData(self):
        print("you tried to export data")

    def close(self):

        pass

    def undo(self):
        print("undo")
        #if self.context.currentImage().posHistory > 0:
        #    self.context.currentImage().posHistory -= 1
        #    self.context.currentImage().image = QtWidgets.QImage(self.context.currentImage().history[self.context.currentImage().posHistory])
        #    self.signals.updateCanvas.emit()
        #    self.signals.resizeCanvas.emit()

    def redo(self):
        print("redo")
        #if self.context.currentImage().posHistory < len(self.context.currentImage().history)-1:
        #    self.context.currentImage().posHistory += 1
        #    self.context.currentImage().image = QtWidgets.QImage(self.context.currentImage().history[self.context.currentImage().posHistory])
        #    self.signals.updateCanvas.emit()
        #    self.signals.resizeCanvas.emit()

    def showHelp(self):
        pass

    def showAboutDialog(self):
        pass

    def showSimToolbar(self):
        self.simWindow.show()

    def showImageToolbar(self):
        log.info("Image toolbar")