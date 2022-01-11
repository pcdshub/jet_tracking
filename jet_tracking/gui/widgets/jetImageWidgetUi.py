from PyQt5.QtWidgets import QVBoxLayout, QGraphicsView, QGraphicsScene
import pyqtgraph as pg
from jetgraphing import ScrollingTimeWidget, graph_setup


class Image_Ui(object):

    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """

        obj.layout = QVBoxLayout(obj)
        obj.setLayout(obj.layout)
        obj.view = QGraphicsView()
        obj.scene = QGraphicsScene()
        #obj.scene.setSceneRect(50, 50, 300, 300)

        obj.layout.addWidget(obj.view)
