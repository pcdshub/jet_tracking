from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QSizePolicy, QHBoxLayout, QMainWindow

from gui.widgets.jetImageWidget import JetImageWidget
from gui.widgets.editorWidget import EditorWidget
import yaml
import logging
import cv2

log = logging.getLogger('pydm')
log.setLevel('CRITICAL')

class JetImageView(QWidget):

    def __init__(self, context, signals):
        super(JetImageView, self).__init__()
        self.signals = signals
        self.context = context
        self.camera = ""
        self.mainLayout = QHBoxLayout()
        self.createImageWidget()
        self.createEditorWidget()
        self.mainLayout.addWidget(self.imageWidget, 75)
        self.mainLayout.addWidget(self.editorWidget, 25)
        self.setLayout(self.mainLayout)
        self.make_connections()

    def make_connections(self):
        self.signals.connectCam.connect(self.find_camera)

    def createImageWidget(self):
        self.imageWidget = JetImageWidget(self.context, self.signals)

    def createEditorWidget(self):
        self.editorWidget = EditorWidget(self.context, self.signals)

    def find_camera(self):
        """
        function for reading the config file and sending that information
        to the widget so that the image will be displayed
        """
        with open("jt_configs.yml", "r") as stream:
            data_loaded = yaml.safe_load(stream)
        for key in data_loaded['pv_map'].keys():
            if key == "jetIm":
                self.camera = data_loaded['pv_map']['jetIm']
        else:
            self.camera = data_loaded['im_loc']

        self.signals.camName.emit(self.camera)
