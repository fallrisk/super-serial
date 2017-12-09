"""
Copyright 2017 Justin Watson

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from PyQt5 import QtCore, QtWidgets, QtGui

class SerialConsoleWidget(QtWidgets.QTextEdit):

    dataWrite = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(SerialConsoleWidget, self).__init__(parent)
        self.local_echo_enabled = False
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.ccp = ControlCharPainter()
        self.ccp.setTextEdit(self)
        self.ruler = Ruler(self)

    def keyPressEvent(self, event):
        ignore_keys = [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right,
            QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Backspace]
        if event.key() in ignore_keys:
            return
        if self.local_echo_enabled:
            super(SerialConsoleWidget, self).keyPressEvent(event)
        self.dataWrite.emit(event.text())

    def putData(self, data):
        self.insertPlainText(data)
        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def paintEvent(self, event):
        margin = 10
        text_layout = QtGui.QTextLayout('The above example demonstrates how simple it is to quickly generate new rich text documents using a minimum amount of code. Although we have generated a crude fixed-pitch calendar to avoid quoting too much code, Scribe provides much more sophisticated layout and formatting features.', self.font())
        fm = QtGui.QFontMetrics(self.font())
        line_height = fm.height()
        y = 0
        radius = min(self.width() / 2.0, self.height() / 2.0) - margin

        text_layout.beginLayout()
        while True:
            line = text_layout.createLine()
            if not line.isValid():
                break

            x1 = max(0.0, pow(pow(radius, 2) - pow(radius - y, 2), 0.5))
            x2 = max(0.0, pow(pow(radius, 2) - pow(radius - (y + line_height), 2), 0.5))
            x = max(x1, x2) + margin
            line_width = (self.width() - margin) - x

            line.setLineWidth(line_width)
            line.setPosition(QtCore.QPointF(x, margin + y))
            y += line.height()

        text_layout.endLayout()

        painter = QtGui.QPainter(self)
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtCore.Qt.white)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.black))
        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        text_layout.draw(painter, QtCore.QPoint(0, 0))

        painter.setBrush(QtGui.QBrush(QtGui.QColor('#a6ce39')))
        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        painter.drawEllipse(QtCore.QRectF(-radius, margin, 2 * radius, 2 * radius))
        painter.end()


class ControlCharPainter(QtCore.QObject):

    def _onContentsChange(self, position, chars_removed, chars_added):
        print('contents changed {} {} {}'.format(position, chars_removed, chars_added))

    def setTextEdit(self, text_edit_widget):
        self._text_edit_widget = text_edit_widget
        self._text_edit_widget.document().contentsChange.connect(self._onContentsChange)


class Ruler(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Ruler, self).__init__(parent)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        size = QtCore.QSizeF(4, 20)
        color = QtGui.QColor(QtCore.Qt.darkGray)
        color.setAlphaF(.5)
        painter.setPen(color)
        x = 40
        painter.drawLine(x, 0, x, size.height())


class SuperTextLayout(QtGui.QTextLayout):
    def draw(self, p, pos, selection):
        # After the regualr draw has completed. I iterate through the text to
        # see if there were any control characters. If there were then I draw
        # draw a rectangle over that area. That previously had a char. or blank in it.
        # This limits my drawing space, but doesn't break anything.
        pass
