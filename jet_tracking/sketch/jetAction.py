from PyQt5.QtGui import QPixmap


class JetImageAction(QPixmap):
    def __init__(self, context, signals):
        super(JetImageAction, self).__init__()
        self.context = context
        self.signals = signals
        self.parent = parent
        self.make_connections()

    def make_connections(self):
        self.signals.imageProcessingRequest.connect(self.find_center)

    def find_center(self):
        pass


"""
NTS:
# Create scene
self.image_item = QGraphicsPixmapItem()
scene = QGraphicsScene(self)
scene.addItem(self.image_item)

# Create GraphicView display
self.view = QGraphicsView(scene, self)
# Adding right click menus
self.view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
self.zoomout_action = QAction("Fit canvas", self)
self.view.addAction(self.zoomout_action)

display camera image:
image = QImage(camera_image, w, h, w, QImage.Format_Grayscale8)
self.image_item.setPixmap(QPixmap.fromImage(image))
self.view.fitInView(self.image_item)
"""
