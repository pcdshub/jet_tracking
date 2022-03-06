import pyqtgraph as pg
from jetGraphing import ScrollingTimeWidget, graph_setup, add_calibration_graph
from PyQt5.QtWidgets import QVBoxLayout


class GraphsUi(object):
    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """

        obj.layout = QVBoxLayout()
        obj.setLayout(obj.layout)
        obj.ratio_graph = ScrollingTimeWidget(obj.context, obj.signals)
        obj.i0_graph = ScrollingTimeWidget(obj.context, obj.signals)
        obj.diff_graph = ScrollingTimeWidget(obj.context, obj.signals)
        graph_setup(obj.ratio_graph, "Intensity Ratio",
                    "I/I\N{SUBSCRIPT ZERO}", pg.mkPen(width=5, color='r'))
        graph_setup(obj.i0_graph, "Initial Intensity", "I\N{SUBSCRIPT ZERO}",
                    pg.mkPen(width=5, color='b'))
        graph_setup(obj.diff_graph, "Intensity at the Detector",
                    "Diffraction Intensity", pg.mkPen(width=5, color='g'))
        add_calibration_graph(obj.ratio_graph)
        add_calibration_graph(obj.i0_graph)
        add_calibration_graph(obj.diff_graph)
        obj.i0_graph.setXLink(obj.ratio_graph)
        obj.diff_graph.setXLink(obj.ratio_graph)
        obj.layout.addWidget(obj.ratio_graph)
        obj.layout.addWidget(obj.i0_graph)
        obj.layout.addWidget(obj.diff_graph)
