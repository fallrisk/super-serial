

from PyQt5 import QtCore, QtWidgets, QtGui

class SerialConsoleWidget(QtWidgets.QPlainTextEdit):

    dataWrite = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(SerialConsoleWidget, self).__init__(parent)
        self.local_echo_enabled = True

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
