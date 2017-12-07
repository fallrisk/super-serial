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

    def keyPressEvent(self, event):
        ignore_keys = [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right,
            QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Backspace]
        if event.key() in ignore_keys:
            return
        if self.local_echo_enabled:
            super(SerialConsoleWidget, self).keyPressEvent(event)
        self.dataWrite.emit(event.text())

    def putData(self, data):
        for c in data:
            if not self.show_crlf:
                self.insertPlainText(c)
                continue
            if c == '\n' or c == '\r':
                ctrlCharFormat = QtGui.QTextCharFormat()
                ctrlCharFormat.setObjectType(ControlCharFormat)
                ctrlCharFormat.setProperty(1, ord(c))
                orc = chr(0xfffc)
                cursor = self.textCursor()
                cursor.insertText(orc, ctrlCharFormat)
                self.setTextCursor(cursor)
                self.insertPlainText(c)
            elif ord(c) < 0x20:
                ctrlCharFormat = QtGui.QTextCharFormat()
                ctrlCharFormat.setObjectType(ControlCharFormat)
                ctrlCharFormat.setProperty(1, ord(c))
                orc = chr(0xfffc)
                cursor = self.textCursor()
                cursor.insertText(orc, ctrlCharFormat)
                self.setTextCursor(cursor)
            else:
                self.insertPlainText(c)
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
