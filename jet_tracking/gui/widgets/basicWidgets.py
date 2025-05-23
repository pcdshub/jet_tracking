from dataclasses import dataclass

from PyQt5 import QtCore
from PyQt5.QtCore import (QAbstractAnimation, QParallelAnimationGroup,
                          QPropertyAnimation, QRect, Qt, pyqtSignal)
from PyQt5.QtGui import QBrush, QColor, QDoubleValidator, QPainter, QPalette
from PyQt5.QtWidgets import (QFrame, QLabel, QLineEdit, QMessageBox,
                             QScrollArea, QSizePolicy, QToolButton,
                             QVBoxLayout, QWidget)


class LineEdit(QLineEdit):
    checkVal = pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = QDoubleValidator()
        self.setValidator(self.validator)
        self.textChanged.connect(self.new_text)
        self.returnPressed.connect(self.check_validator)
        self.ntext = self.text()

    def new_text(self, text):
        if self.hasAcceptableInput():
            self.ntext = text

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Return and not self.hasAcceptableInput():
            self.check_validator()

    def check_validator(self):
        try:
            if float(self.text()) > self.validator.top():
                self.setText(str(self.validator.top()))
            elif float(self.text()) < self.validator.bottom():
                self.setText(str(self.validator.bottom()))
        except ValueError:
            QMessageBox.about(self, "Error", "Input can only be a number")
            self.setText(self.ntext)
        self.checkVal.emit(float(self.ntext))

    def valRange(self, x1, x2):
        self.validator.setRange(x1, x2)
        self.validator.setDecimals(6)
        self.validator.setNotation(QDoubleValidator.StandardNotation)


class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.toggle_button = QToolButton(
            text=title, checkable=True, checked=False
        )
        # self.toggle_button.setStyleSheet("QToolButton {border: none;\
        #         border: 1px solid #FF17365D;\
        #         border-top-left-radius: 15px;\
        #         border-top-right-radius: 15px;\
        #         background-color: #FF17365D;\
        #         padding: 5px 0px;\
        #         color: rgb(255, 255, 255);\
        #         max-height: 30px;\
        #         font-size: 14px;\
        #     }\
        #     QToolButton:hover {\
        #         background-color: lightgreen;\
        #         color: black;\
        #     }")
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QParallelAnimationGroup(self)

        self.content_area = QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            Qt.DownArrow if not checked else Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QAbstractAnimation.Forward
            if not checked
            else QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def clear_layout(self, layout):
        try:
            for i in reversed(range(layout.count())):
                widgetToRemove = layout.itemAt(i).widget()
                layout.removeWidget(widgetToRemove)
                widgetToRemove.setPArent(None)
        except AttributeError:
            pass

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        self.clear_layout(lay)
        self.content_area.setLayout(layout)
        collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


class Label(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setTitleStylesheet(self):
        self.setStyleSheet("\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                border-top-left-radius: 15px;\
                border-top-right-radius: 15px;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                max-height: 35px;\
                font-size: 14px;\
            ")

    def setSubtitleStyleSheet(self):
        self.setStyleSheet("\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                background-color: #FF17365D;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                font-size: 12px;\
            ")

    def setTrackingStylesheet(self):
        # this will change based on the status given back
        self.setStyleSheet("\
                qproperty-alignment: AlignCenter;\
                border: 1px solid #FF17365D;\
                background-color: red;\
                padding: 5px 0px;\
                color: rgb(255, 255, 255);\
                font-size: 12px;\
            ")


class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class QVLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


def _left_thumb_adjuster(value, min_value):
    if value < min_value:
        value = min_value


def _right_thumb_adjuster(value, max_value):
    if value > max_value:
        value = max_value


@dataclass
class Thumb:
    """Thumb class which holds information about a thumb.
    """
    value: int
    rect: QRect
    pressed: bool


class QRangeSlider(QWidget):
    """
        QtRangeSlider is a class which implements a slider with 2 thumbs.
        Methods
            * __init__ (self, QWidget parent, left_value, right_value,
                        left_thumb_value=0, right_thumb_value=None)
            * set_left_thumb_value (self, int value):
            * set_right_thumb_value (self, int value):
            * (int) get_left_thumb_value (self):
            * (int) get_right_thumb_value (self):
        Signals
            * left_thumb_value_changed (int)
            * right_thumb_value_changed (int)
    """
    HEIGHT = 20
    WIDTH = 250
    THUMB_WIDTH = 12
    THUMB_HEIGHT = 12
    TRACK_HEIGHT = 5
    TRACK_COLOR = QColor(0xc7, 0xc7, 0xc7)
    TRACK_FILL_COLOR = QColor(0x01, 0x81, 0xff)
    TRACK_PADDING = THUMB_WIDTH // 2 + 1
    TICK_PADDING = 1

    left_thumb_value_changed = pyqtSignal('unsigned long long')
    right_thumb_value_changed = pyqtSignal('unsigned long long')
    valueChanged = pyqtSignal(list)
    valueMoving = pyqtSignal(list)
    sliderReleased = pyqtSignal()

    def __init__(self, parent=None, left_value=0, right_value=255,
                 left_thumb_value=0, right_thumb_value=255):
        super().__init__(parent)

        self.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )
        self.setMinimumWidth(self.WIDTH)
        self.setMinimumHeight(self.HEIGHT)

        self._left_value = left_value
        self._right_value = right_value

        self._left_thumb = Thumb(left_thumb_value, None, False)
        _right_thumb_value = (right_thumb_value if right_thumb_value
                              is not None else self._right_value)
        if _right_thumb_value < left_thumb_value + 1:
            raise ValueError("Right thumb value is less or equal to left thumb"
                             " value.")
        self._right_thumb = Thumb(_right_thumb_value, None, False)

        self._canvas_width = None
        self._canvas_height = None

        self._ticks_count = 0

        parent_palette = parent.palette()
        self._background_color = parent_palette.color(QPalette.Window)
        self._base_color = parent_palette.color(QPalette.Base)
        self._button_color = parent_palette.color(QPalette.Button)
        self._border_color = parent_palette.color(QPalette.Mid)

    def setMaximum(self, value):
        self._right_value = value
        self._right_thumb.value = value

    def setMinimum(self, value):
        self._left_value = value
        self._left_thumb.value = value

    def paintEvent(self, unused_e):
        # print("paintEvent")
        del unused_e
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.__draw_track(self._canvas_width, self._canvas_height, painter)
        self.__draw_track_fill(self._canvas_width, self._canvas_height,
                               painter)
        self.__draw_ticks(self._canvas_width, self._canvas_height, painter,
                          self._ticks_count)
        self.__draw_left_thumb(self._canvas_width, self._canvas_height,
                               painter)
        self.__draw_right_thumb(self._canvas_width, self._canvas_height,
                                painter)

        painter.end()

    def __get_track_y_position(self):
        return self._canvas_height // 2 - self.TRACK_HEIGHT // 2

    def __draw_track(self, canvas_width, canvas_height, painter):
        del canvas_height
        brush = QBrush()
        brush.setColor(self.TRACK_COLOR)
        brush.setStyle(Qt.SolidPattern)

        rect = QRect(self.TRACK_PADDING, self.__get_track_y_position(),
                     canvas_width - 2 * self.TRACK_PADDING, self.TRACK_HEIGHT)
        painter.fillRect(rect, brush)

    def __draw_track_fill(self, canvas_width, canvas_height, painter):
        del canvas_height
        brush = QBrush()
        brush.setColor(self.TRACK_FILL_COLOR)
        brush.setStyle(Qt.SolidPattern)

        available_width = canvas_width - 2 * self.TRACK_PADDING
        x1 = (self._left_thumb.value / self._right_value * available_width
              + self.TRACK_PADDING)
        x2 = (self._right_thumb.value / self._right_value * available_width
              + self.TRACK_PADDING)
        rect = QRect(round(x1), self.__get_track_y_position(),
                     round(x2) - round(x1), self.TRACK_HEIGHT)
        painter.fillRect(rect, brush)

    # pylint: disable=no-self-use
    def __set_painter_pen_color(self, painter, pen_color):
        pen = painter.pen()
        pen.setColor(pen_color)
        painter.setPen(pen)

    def __draw_thumb(self, x, y, painter):
        brush = QBrush()
        brush.setColor(self._base_color)
        brush.setStyle(Qt.SolidPattern)

        self.__set_painter_pen_color(painter, self._border_color)

        painter.setBrush(brush)

        thumb_rect = QRect(round(x) - self.THUMB_WIDTH // 2
                           + self.TRACK_PADDING, y + self.TRACK_HEIGHT // 2
                           - self.THUMB_HEIGHT // 2, self.THUMB_WIDTH,
                           self.THUMB_HEIGHT)
        painter.drawEllipse(thumb_rect)
        return thumb_rect

    def __draw_right_thumb(self, canvas_width, canvas_height, painter):
        del canvas_height
        available_width = canvas_width - 2 * self.TRACK_PADDING
        x = self._right_thumb.value / self._right_value * available_width
        y = self.__get_track_y_position()
        self._right_thumb.rect = self.__draw_thumb(x, y, painter)

    def __draw_left_thumb(self, canvas_width, canvas_height, painter):
        del canvas_height
        available_width = canvas_width - 2 * self.TRACK_PADDING
        x = round(self._left_thumb.value / self._right_value * available_width)
        y = self.__get_track_y_position()
        self._left_thumb.rect = self.__draw_thumb(x, y, painter)

    def set_left_thumb_value(self, value):
        if value < 0 or value > self._right_thumb.value - 1:
            return
        if value == self._left_thumb.value:
            # nothing to update
            return
        self._left_thumb.value = value
        # print(f"value before emit {value}")
        self.left_thumb_value_changed.emit(value)

        self.repaint()

    def set_right_thumb_value(self, value):
        if value > self._right_value or value < self._left_thumb.value + 1:
            return
        if value == self._right_thumb.value:
            # nothing to update
            return
        self._right_thumb.value = value
        # print(f"value before emit {value}")
        self.right_thumb_value_changed.emit(value)

        self.repaint()

    # override Qt event
    def mousePressEvent(self, event):
        # print("mousePressEvent")
        if self._left_thumb.rect.contains(event.x(), event.y()):
            self._left_thumb.pressed = True
        if self._right_thumb.rect.contains(event.x(), event.y()):
            self._right_thumb.pressed = True
        super().mousePressEvent(event)
        self.valueMoving.emit([self.get_left_thumb_value(),
                               self.get_right_thumb_value()])

    # override Qt event
    def mouseReleaseEvent(self, event):
        # print("mouseReleaseEvent")
        self._left_thumb.pressed = False
        self._right_thumb.pressed = False
        self.valueChanged.emit([self.get_left_thumb_value(),
                                self.get_right_thumb_value()])
        super().mouseReleaseEvent(event)
        self.sliderReleased.emit()

    # pylint: disable=no-self-use
    def __get_thumb_value(self, x, canvas_width, right_value):
        # print(f"x {x} canvas_width {canvas_width} left_value "
        #       f"{self._left_thumb.value} right_value {right_value}")
        return round(x / canvas_width * right_value)

    # override Qt event
    def mouseMoveEvent(self, event):
        # print("mouseMoveEvent")

        thumb = (self._left_thumb if self._left_thumb.pressed
                 else self._right_thumb)

        if thumb.pressed:
            new_val = self.__get_thumb_value(event.x(), self._canvas_width,
                                             self._right_value)
            if thumb == self._left_thumb:
                value_setter = self.set_left_thumb_value
                _left_thumb_adjuster(new_val, 0)
            else:
                value_setter = self.set_right_thumb_value
                _right_thumb_adjuster(new_val, self._right_value)
            value_changed = new_val != thumb.value
            if value_changed:
                value_setter(new_val)

        super().mouseMoveEvent(event)
        self.valueMoving.emit([self.get_left_thumb_value(),
                               self.get_right_thumb_value()])

    def get_left_thumb_value(self):
        return self._left_thumb.value

    def get_right_thumb_value(self):
        return self._right_thumb.value

    def set_ticks_count(self, count):
        if count < 0:
            raise ValueError("Invalid ticks count.")
        self._ticks_count = count

    def __draw_ticks(self, canvas_width, canvas_height, painter, ticks_count):
        del canvas_height
        if not self._ticks_count:
            return

        self.__set_painter_pen_color(painter, self._border_color)

        tick_step = (canvas_width - 2 * self.TRACK_PADDING) // ticks_count
        y1 = self.__get_track_y_position() - self.TICK_PADDING
        y2 = y1 - self.THUMB_HEIGHT // 2
        for x in range(0, ticks_count + 1):
            x = x * tick_step + self.TRACK_PADDING
            painter.drawLine(x, y1, x, y2)

    def resizeEvent(self, event):
        # print("resizeEvent")
        del event
        self._canvas_width = self.width()
        self._canvas_height = self.height()

    def setOrientation(self, orientation):
        pass
