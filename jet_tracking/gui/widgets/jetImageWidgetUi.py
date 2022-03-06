from PyQt5.QtWidgets import QVBoxLayout, QGraphicsView, QGraphicsScene


class Image_Ui(object):

    def setupUi(self, obj):
        """Used to setup the layout and initialize graphs."""

        obj.layout = QVBoxLayout(obj)
        obj.setLayout(obj.layout)
        obj.view = QGraphicsView()
        obj.scene = QGraphicsScene()

        obj.layout.addWidget(obj.view)
