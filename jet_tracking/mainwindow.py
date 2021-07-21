from pydm import Display
from signals import Signals
from PyQt5.QtWidgets import (
                            QMainWindow, QApplication, QVBoxLayout,
                            QScrollArea, QStatusBar, QAction,
                            QDockWidget, QSizePolicy
                            )
from PyQt5.QtCore import QSize, Qt, QCoreApplication 
from signals import Signals
from context import Context
from mainwidget import GraphsWidget, ControlsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.signals = Signals()
        self.context = Context()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Jet Tracking")
        self.statusBar = self.statusBar
        self.menuBar = self.createMenuBar()
        self.createDockWidgets()
        self.ctrlPressed = False
        #self.central_scroll = QScrollArea()
        self.widget_central = GraphsWidget(self.context, self.signals)
        #self.central_scroll.setWidget(self.widget_central)
        self.setCentralWidget(self.widget_central)

    def minimumSizeHint(self):
        return(QSize(1400, 800))

    def ui_filepath(self):
        pass

    def load_data(self):
        pass

    def createFileActions(self):

        ids = [ "open", "export", "exit"]
        tips = ["open exported file to run in simulation mode", "export all or some data",
                " exit the application"]
        shortcuts = ['Ctrl+O', 'Ctrl+Shift+E', 'Ctrl+Q']
        connects = [self.openFile, self.exportData, self.close]

        L = []

        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.triggered.connect(self.restoreFocus)
            a.setStatusTip(tips[i])
            if connects[i] != 0: a.triggered.connect(connects[i])
            L.append(a)

        L.insert(3,0) # Los ceros simbolizan separadores

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
            a.triggered.connect(self.restoreFocus)
            a.setStatusTip(tips[i])
            if connects[i] != 0: a.triggered.connect(connects[i])
            L.append(a)

        L.insert(2,0)

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

        L.insert(1,0) 

        return L

    def createMenuBar(self):
        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("file")
        editMenu = menubar.addMenu("edit")
        helpMenu = menubar.addMenu("help")
        fileActions = self.createFileActions()
        editActions = self.createEditActions()
        helpActions = self.createHelpActions()
        for i in fileActions:
            if i == 0: fileMenu.addSeparator()
            else: fileMenu.addAction(i)
        for i in editActions:
            if i == 0: editMenu.addSeparator()
            else: editMenu.addAction(i)
        for i in helpActions:
            if i == 0: helpMenu.addSeparator()
            else: helpMenu.addAction(i)

        return menubar

    def createDockWidgets(self):
        self.setDockNestingEnabled(True)
        #self.setCorner(Qt.BottomRightCorner, Qt.BottomDockWidget) #test at some point to see how it behaves
        # Controls widget
        self.controlsDock = QDockWidget("Controls", self)
        self.controlsDock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.controlsDock.setFeatures(QDockWidget.DockWidgetFloatable)
        
        #########################################
        # need a CONTROLS class
        #########################################

        self.controlsWidget = ControlsWidget(self.context, self.signals)
        self.controlsDock.setWidget(self.controlsWidget)
        self.controlsDock.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.addDockWidget(Qt.RightDockWidgetArea, self.controlsDock)
        self.resizeDocks([self.controlsDock], [30], Qt.Horizontal)
        # Jet Image Widget
        #self.jetImageDock = QtWidgets.QDockWidget("Jet Image", self)
        #self.jetImageDock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        #self.jetImageDock.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable)
        #jetImageWidget = JetImageWidget(self, self.context, self.signals)
        #self.jetImageWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        #self.addDockWidget(Qt.BottomDockWidgetArea, self.jetImageWidget)

    def restoreFocus(self):

        print("Restoring Focus")
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
    """
    def keyPressEvent(self, event):

        super(MainWindow, self).keyPressEvent(event)

        if event.key() == Qt.Key_Control:
            print("Control Pressed")
            self.ctrlPressed = True
            QtCore.QCoreApplication.instance().setOverrideCursor(self.context.colorPickerCur)
            self.signals.ctrlPressed.emit()
            self.grabMouse()
            self.grabKeyboard()

        elif event.key() == Qt.Key_Plus:
            if self.context.currentTool == 1:
                self.context.setPencilSize(self.context.pencilSize+1)
            elif self.context.currentTool == 2:
                self.context.setEraserSize(self.context.eraserSize+1)

        elif event.key() == Qt.Key_Minus:
            if self.context.currentTool == 1:
                self.context.setPencilSize(self.context.pencilSize-1)
            elif self.context.currentTool == 2:
                self.context.setEraserSize(self.context.eraserSize-1)

        else:
            QtCore.QCoreApplication.instance().restoreOverrideCursor()
            self.releaseMouse()
            self.releaseKeyboard()

    def keyReleaseEvent(self, event):

        super(MainWindow, self).keyReleaseEvent(event)

        if event.key() == Qt.Key_Control:
            self.ctrlPressed = False
            QtCore.QCoreApplication.instance().restoreOverrideCursor()
            self.releaseMouse()
            self.releaseKeyboard()

    def mousePressEvent(self, event):

        super(MainWindow, self).mousePressEvent(event)

        if self.ctrlPressed:
            print("Picking Desktop Color")
            widget = QtCore.QCoreApplication.instance().desktop().screen()
            im = QtWidgets.QPixmap.grabWindow(widget.winId()).toImage() 
            c = QtWidgets.QColor(im.pixel(QtWidgets.QCursor.pos())) 
            if event.button() == Qt.LeftButton:
                self.context.changePrimaryColor(c) 
            elif event.button() == Qt.RightButton:
                self.context.changeSecondaryColor(c)

    def mouseMoveEvent(self, event):

        super(MainWindow, self).mouseMoveEvent(event)

        if self.ctrlPressed:
            widget = QtCore.QCoreApplication.instance().desktop().screen()
            im = QtWidgets.QPixmap.grabWindow(widget.winId()).toImage() 
            c = QtWidgets.QColor(im.pixel(QtWidgets.QCursor.pos())) 
            if event.buttons() == Qt.LeftButton:
                self.context.changePrimaryColor(c) 
            elif event.buttons() == Qt.RightButton:
                self.context.changeSecondaryColor(c) 

    def wheelEvent(self, event):

        if self.ctrlPressed:
            if event.delta() > 0:
                self.zoomIn()
            else:
                self.zoomOut()

        super(MainWindow, self).wheelEvent(event)
    """
    def closeEvent(self, event):
        """
        l = []
        for i in range(len(self.context.images)):
            if self.context.images[i].modified: l.append(i)

        if len(l) > 0:
            reply = QtWidgets.QMessageBox.warning(self, self.context.getText("dialog_exit", "title"),
                self.context.getText("dialog_exit", "message"),
                QtWidgets.QMessageBox.SaveAll | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Discard:
                event.accept()
            elif reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()  
                return
            elif reply == QtWidgets.QMessageBox.SaveAll:
                for i in l:
                    self.mainWidget.setCurrentIndex(i)
                    self.context.setCurrentImagePos(i)
                    self.saveFile()
                event.accept()
                return

            

        self.context.saveDefaults()
        """
        super(MainWindow, self).closeEvent(event)
