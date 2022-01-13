from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QVBoxLayout


class Image_Ui(object):

    def setupUi(self, obj):
        """Used to setup the layout and initialize graphs."""

        obj.layout = QVBoxLayout(obj)
        obj.setLayout(obj.layout)
        obj.view = QGraphicsView()
        obj.scene = QGraphicsScene()
        # obj.scene.setSceneRect(50, 50, 300, 300)

        obj.layout.addWidget(obj.view)
