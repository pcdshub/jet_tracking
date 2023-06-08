from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsScene
from PyQt5.QtCore import QPointF, Qt, pyqtSignal
from PyQt5.QtGui import QPen


class GraphicsScene(QGraphicsScene):
    itemPos = pyqtSignal()


class HLineItem(QGraphicsLineItem):

    def __init__(self):
        super().__init__()
        self.setPen(QPen(Qt.red, 3))
        self.setFlags(self.ItemIsMovable | self.ItemIsSelectable)
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptHoverEvents(True)

    def mouseMoveEvent(self, event):
        orig_cursor_position = event.lastScenePos()
        updated_cursor_position = event.scenePos()

        orig_position = self.scenePos()
        updated_cursor_y = updated_cursor_position.y() - orig_cursor_position.y() + orig_position.y()
        self.setPos(QPointF(orig_position.x(), updated_cursor_y))

    def mouseReleaseEvent(self, event):
        self.scene().itemPos.emit()


class VLineItem(QGraphicsLineItem):

    def __init__(self):
        super(VLineItem, self).__init__()
        self.setPen(QPen(Qt.blue, 3))
        self.setFlag(QGraphicsLineItem.ItemIsMovable)
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptHoverEvents(True)

    def mouseMoveEvent(self, event):
        orig_cursor_position = event.lastScenePos()
        updated_cursor_position = event.scenePos()

        orig_position = self.scenePos()
        updated_cursor_x = updated_cursor_position.x() - orig_cursor_position.x() + orig_position.x()
        self.setPos(QPointF(updated_cursor_x, orig_position.y()))

    def mouseReleaseEvent(self, event):
        self.scene().itemPos.emit()
