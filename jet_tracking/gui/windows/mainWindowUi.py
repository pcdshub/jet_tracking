from PyQt5.QtWidgets import QMenuBar


class Ui_MainWindow(object):
    def setupUi(self, obj):
        obj.setObjectName("Jet Tracking")
        obj.menubar = QMenuBar()
        obj.fileMenu = obj.menubar.addMenu("file")
        obj.editMenu = obj.menubar.addMenu("edit")
        obj.helpMenu = obj.menubar.addMenu("help")
        obj.toolMenu = obj.menubar.addMenu("tools")
        obj.setMenuBar(obj.menubar)
