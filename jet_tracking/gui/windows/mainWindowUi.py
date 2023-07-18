from PyQt5.QtWidgets import QMenuBar


class Ui_MainWindow:
    """This class represents the user interface (UI) definition for the main window of the application."""
    def setupUi(self, obj):
        """
        Method for setting up the UI elements of the main window.

        Parameters
        ----------
        obj (QMainWindow): The main window object.

        he setupUi method performs the following actions:
        Sets the object name of the main window.
        Creates a menu bar and assigns it to the obj.menubar attribute.
        Creates four menus ("file", "edit", "help", and "tools") and adds them to the menu bar using the addMenu method.
        Sets the menu bar for the main window using the setMenuBar method.
        """
        obj.setObjectName("Jet Tracking")
        obj.menubar = QMenuBar()
        obj.fileMenu = obj.menubar.addMenu("file")
        obj.editMenu = obj.menubar.addMenu("edit")
        obj.helpMenu = obj.menubar.addMenu("help")
        obj.toolMenu = obj.menubar.addMenu("tools")
        obj.setMenuBar(obj.menubar)
