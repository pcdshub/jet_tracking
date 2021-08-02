from PyQt5.QtWidgets import  QAction, QMenuBar
from PyQt5.QtCore import QSize, QCoreApplication
import logging
from gui.windows.simulationWindow import SimWindow

log = logging.getLogger(__name__)

class Ui_MainWindow(object):
    def setupUi(self, obj):
        obj.setMinimumSize(self.minimumSizeHint())
        obj.setObjectName("Jet Tracking")
        obj.menubar = QMenuBar()
        obj.fileMenu = obj.menubar.addMenu("file")
        obj.editMenu = obj.menubar.addMenu("edit")
        obj.helpMenu = obj.menubar.addMenu("help")
        obj.toolMenu = obj.menubar.addMenu("tools")
        obj.setMenuBar(obj.menubar)

    def minimumSizeHint(self):
        return (QSize(1400, 800))



