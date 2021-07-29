from PyQt5.QtWidgets import  QAction, QLabel
from PyQt5.QtCore import QSize, QCoreApplication
import logging

log = logging.getLogger(__name__)

class Ui_MainWindow(object):
    def setupUi(self, obj):
        obj.setMinimumSize(self.minimumSizeHint())
        obj.setObjectName("Jet Tracking")
        self.menuBar = self.createMenuBar()
        self.ctrlPressed = False

    def minimumSizeHint(self):
        return (QSize(1400, 800))

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

    def createMenuBar(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("file")
        editMenu = menubar.addMenu("edit")
        helpMenu = menubar.addMenu("help")
        toolMenu = menubar.addMenu("tools")
        fileActions = self.createFileActions()
        editActions = self.createEditActions()
        helpActions = self.createHelpActions()
        toolActions = self.createToolActions()
        for i in fileActions:
            if i == 0:
                fileMenu.addSeparator()
            else:
                fileMenu.addAction(i)
        for i in editActions:
            if i == 0:
                editMenu.addSeparator()
            else:
                editMenu.addAction(i)
        for i in helpActions:
            if i == 0:
                helpMenu.addSeparator()
            else:
                helpMenu.addAction(i)
        for i in toolActions:
            if i == 0:
                toolMenu.addSeparator()
            else:
                toolMenu.addAction(i)

        return menubar

    def restoreFocus(self):

        log.info("Restoring Focus")
        self.ctrlPressed = False
        self.releaseMouse()
        self.releaseKeyboard()
        QCoreApplication.instance().restoreOverrideCursor()

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
        log.info("simulation toolbar")

    def showImageToolbar(self):
        log.info("Image toolbar")
