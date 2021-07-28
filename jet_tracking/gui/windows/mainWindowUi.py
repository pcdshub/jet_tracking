from PyQt5.QtWidgets import  QAction, QLabel
from PyQt5.QtCore import QSize


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

        L = []

        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.setStatusTip(tips[i])


        L.insert(3, 0)  # Los ceros simbolizan separadores

        return L

    def createEditActions(self):
        ids = ["undo", "redo"]
        shortcuts = ['Ctrl+Z', 'Ctrl+Y']
        tips = ["undo last action", "redo last action"]
        L = []

        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            a.setStatusTip(tips[i])

        L.insert(2, 0)

        return L

    def createHelpActions(self):

        ids = ["contents", "about"]
        shortcuts = ['F1', 'Ctrl+B']

        L = []

        for i in range(len(ids)):
            a = QAction(ids[i], self)
            a.setShortcut(shortcuts[i])
            L.append(a)

        L.insert(1, 0)

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

        return menubar