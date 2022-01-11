from PyQt5.QtWidgets import QVBoxLayout
import pyqtgraph as pg
from jetgraphing import ScrollingTimeWidget, graph_setup, add_calibration_graph


class Graphs_Ui(object):

    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """

        obj.layout = QVBoxLayout()
        obj.setLayout(self.layout)
        obj.ratio_graph = ScrollingTimeWidget(self.context, self.signals)
        obj.i0_graph = ScrollingTimeWidget(self.context, self.signals)
        obj.diff_graph = ScrollingTimeWidget(self.context, self.signals)
        graph_setup(obj.ratio_graph, "Intensity Ratio", f"I/I\N{SUBSCRIPT ZERO}", \
                        pg.mkPen(width=5, color='r'))
        graph_setup(obj.i0_graph, "Initial Intensity", f"I\N{SUBSCRIPT ZERO}", \
                        pg.mkPen(width=5, color='b'))
        graph_setup(obj.diff_graph, "Intensity at the Detector", "Diffraction Intensity", \
                        pg.mkPen(width=5, color='g'))
        add_calibration_graph(self.ratio_graph)
        add_calibration_graph(self.i0_graph)
        add_calibration_graph(self.diff_graph)
        obj.i0_graph.setXLink(obj.ratio_graph)
        obj.diff_graph.setXLink(obj.ratio_graph)
        obj.layout.addWidget(obj.ratio_graph)
        obj.layout.addWidget(obj.i0_graph)
        obj.layout.addWidget(obj.diff_graph)
