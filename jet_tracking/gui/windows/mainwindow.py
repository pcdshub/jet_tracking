from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QTabWidget, QAction, QMainWindow, QLabel
from jet_tracking.context import Context
from jet_tracking.gui.views.jetTrackerView import JetTrackerView
from jet_tracking.gui.windows.mainWindowUi import Ui_MainWindow
from jet_tracking.signals import Signals
import logging

log = logging.getLogger(__name__)

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setAttribute(Qt.WA_AlwaysStackOnTop)
        self.context = Context()
        self.signals = Signals()
        self.setupUi(self)

        self.create_views_and_dialogs()
        self.setup_window_tabs()
        self.connect_buttons()
        self.connect_signals()

    def setup_window_tabs(self):
        # self.setDockNestingEnabled(True)
        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.addTab(self.jetTrackerView, "Jet Tracker")


    def create_views_and_dialogs(self):
        self.jetTrackerView = JetTrackerView(self.context, self.signals)
        # self.helpDialog = HelpDialog()

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