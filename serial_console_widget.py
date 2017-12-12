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

class SerialConsoleWidget(QtWidgets.QPlainTextEdit):

    dataWrite = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(SerialConsoleWidget, self).__init__(parent)
        self.local_echo_enabled = False
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.ccp = ControlCharPainter()
        self.ccp.setTextEdit(self)
        #self.ruler = Ruler(self)
        #self.my_layout = SuperTextLayout(self.document())
        #self.document().setDocumentLayout(SuperTextLayout(self.document()))

        #layout = SuperTextLayout(self.document())
        #self.document().setDocumentLayout(layout)

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


class ControlCharPainter(QtCore.QObject):

    def _onContentsChange(self, position, chars_removed, chars_added):
        print('contents changed {} {} {}'.format(position, chars_removed, chars_added))
        print(self._text_edit_widget.document().documentLayout())

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


class SuperTextLayout(QtWidgets.QPlainTextDocumentLayout):
    def draw(self, p, pos, selections, clip):
        # After the regualr draw has completed. I iterate through the text to
        # see if there were any control characters. If there were then I draw
        # draw a rectangle over that area. That previously had a char. or blank in it.
        # This limits my drawing space, but doesn't break anything.
        super(SuperTextLayout, self).draw(p, pos, selections, clip)
        print('draw')

    def draw(p, paint_context):
        print('draw2')


class SuperRawFont(QtGui.QRawFont):
    def pathForGlyph(glyphIndex):
        # if glyphIndex <= 31:
        #     #return my custom path
        #     # http://doc.qt.io/qt-5/qpainterpath.html#addText
        #     rectangle = QRectF()
        #     path = QPainterPath()
        #     path.addRect(rectangle)
        #     print('here')
        # else:
        print('here')
        return super(SuperRawFont, self).pathForGlyph(glyphIndex)
