import pyqtgraph as pg
from PyQt5.QtWidgets import QVBoxLayout


class GraphsUi:
    def setupUi(self, obj):
        """
        used to setup the layout and initialize graphs
        """

        obj.layout = QVBoxLayout()
        obj.setLayout(obj.layout)
        obj.graph1 = pg.PlotWidget()
        obj.graph2 = pg.PlotWidget()
        obj.graph3 = pg.PlotWidget()
        styles = {"color": "#f00", "font-size": "20px"}
        obj.graph1.setLabel("left", "Signal", **styles)
        obj.graph1.setLabel("bottom", "Seconds", **styles)
        obj.graph1.setTitle("Diff")
        obj.graph1.showGrid(x=True, y=True)
        obj.graph2.setLabel("left", "Signal", **styles)
        obj.graph2.setLabel("bottom", "Seconds", **styles)
        obj.graph2.setTitle("I0")
        obj.graph2.showGrid(x=True, y=True)
        obj.graph3.setLabel("left", "Signal", **styles)
        obj.graph3.setLabel("bottom", "Seconds", **styles)
        obj.graph3.setTitle("Ratio")
        obj.graph3.showGrid(x=True, y=True)
        # obj.ratio_graph = ScrollingTimeWidget(obj.context, obj.signals)
        # obj.i0_graph = ScrollingTimeWidget(obj.context, obj.signals)
        # obj.diff_graph = ScrollingTimeWidget(obj.context, obj.signals)
        # graph_setup(obj.ratio_graph, "Intensity Ratio",
        #             "I/I\N{SUBSCRIPT ZERO}", pg.mkPen(width=5, color='r'))
        # graph_setup(obj.i0_graph, "Initial Intensity", "I\N{SUBSCRIPT ZERO}",
        #             pg.mkPen(width=5, color='b'))
        # graph_setup(obj.diff_graph, "Intensity at the Detector",
        #             "Diffraction Intensity", pg.mkPen(width=5, color='g'))
        # add_calibration_graph(obj.ratio_graph)
        # add_calibration_graph(obj.i0_graph)
        # add_calibration_graph(obj.diff_graph)
        # obj.i0_graph.setXLink(obj.ratio_graph)
        # obj.diff_graph.setXLink(obj.ratio_graph)
        obj.layout.addWidget(obj.graph1)
        obj.layout.addWidget(obj.graph2)
        obj.layout.addWidget(obj.graph3)
