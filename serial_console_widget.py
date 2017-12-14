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


ControlCharFormat = QtGui.QTextFormat.UserObject + 1


class SerialConsoleWidget(QtWidgets.QTextEdit):

    dataWrite = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(SerialConsoleWidget, self).__init__(parent)
        self.local_echo_enabled = False
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.show_crlf = False
        self.ccp = ControlCharPainter()
        self.ccp.setTextEdit(self)
        #self.unicode_font = QtGui.QFont('Segoe UI Symbol', 12)

        self.__highligter = Highlighter(self)
        self.__highlight_timer = QtCore.QTimer(self)
        self.__highlight_timer.timeout.connect(self.__highligter.highlight)
        self.__highlight_timer.start(1000)

        # TODO: Run highlight once every time new data is provided for the widget.

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
        # for c in data:
        #     print(ord(c))
        #     # if not self.show_crlf:
        #     #     self.insertPlainText(c)
        #     #     continue
        #     if c == '\n' or c == '\r':
        #         # ctrlCharFormat = QtGui.QTextCharFormat()
        #         # ctrlCharFormat.setObjectType(ControlCharFormat)
        #         # ctrlCharFormat.setProperty(1, ord(c))
        #         # orc = chr(0xfffc)
        #         # cursor = self.textCursor()
        #         # cursor.insertText(orc, ctrlCharFormat)
        #         # self.setTextCursor(cursor)
        #         self.insertPlainText(c)
        #     elif ord(c) < 0x20:
        #         #ctrlCharFormat = QtGui.QTextCharFormat()
        #         #ctrlCharFormat.setObjectType(ControlCharFormat)
        #         #ctrlCharFormat.setProperty(1, ord(c))
        #         #orc = chr(0xfffc)
        #         prev_font = self.font()
        #         #self.setFont(self.unicode_font)
        #         print('changing char')
        #         cursor = self.textCursor()
        #         nc = chr(ord(c) + 2400)
        #         self.insertPlainText(nc)
        #         self.setFont(prev_font)
        #         #cursor.insertText(orc, ctrlCharFormat)
        #         self.setTextCursor(cursor)
        #     else:
        self.insertPlainText(data)
        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())


class ControlCharObject(QtCore.QObject, QtGui.QTextObjectInterface):
    """
    Refer to the "Text Object Example".
    """
    def intrinsicSize(self, doc, posInDocument, format):
        return QtCore.QSizeF(10, 10)

    def drawObject(self, painter, rect, doc, posInDocument, format):
        x = format.property(1)
        #print('char is 0x{:0x}'.format(x))
        painter.drawRect(QtCore.QRect(rect.x(), rect.y(), 10, 10))


class ControlCharPainter(QtCore.QObject):

    def _onContentsChange(self, position, chars_removed, chars_added):
        #print('contents changed {} {} {}'.format(position, chars_removed, chars_added))
        #print(self._text_edit_widget.document().documentLayout())
        return

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


class Highlighter(QtCore.QObject):
    def __init__(self, parent):
        super(Highlighter, self).__init__()
        self.__parent = parent

    def highlight(self):
        """
        This should be attached to a QTimer.
        """
        char_format = QtGui.QTextCharFormat()
        cursor = self.__parent.textCursor()
        # Format properties are in the following to classes.
        # http://doc.qt.io/qt-5/qtextformat.html#public-functions
        # http://doc.qt.io/qt-5/qtextcharformat.html
        char_format.setForeground(QtGui.QBrush(QtGui.QColor('red')))
        pattern = 'FW'
        # http://doc.qt.io/qt-5/qregexp.html
        regex = QtCore.QRegExp(pattern)
        pos = 0
        index = regex.indexIn(self.__parent.toPlainText(), pos)
        while index != -1:
            # Select the matched text and apply the format.
            #print(index, index + regex.matchedLength())
            cursor.setPosition(index)
            cursor.setPosition(index + regex.matchedLength(), QtGui.QTextCursor.KeepAnchor)
            # http://doc.qt.io/qt-5/richtext-cursor.html
            cursor.mergeCharFormat(char_format)
            # Move to the next match.
            pos = index + regex.matchedLength()
            index = regex.indexIn(self.__parent.toPlainText(), pos)
