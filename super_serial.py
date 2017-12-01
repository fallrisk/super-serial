"""
Copyright Justin Watson 2017

References
* http://pyqt.sourceforge.net/Docs/PyQt5/modules.html#ref-module-index

"""

import argparse
import code
import imp
import io
import json
import os.path as osp
import re
import sys

from types import CodeType

from PyQt5 import QtCore, QtWidgets, QtSerialPort, QtGui
from PyQt5.Qt import QDesktopServices, QUrl

import console

# http://pyqt.sourceforge.net/Docs/PyQt5/gotchas.html#crashes-on-exit
app = None

# TODO: Set to default preferences.
preferences = None

_super_serial_version = 'v0.1.0'

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Super Serial")

        script_dir = osp.dirname(osp.realpath(__file__))
        app_icon = QtGui.QIcon(script_dir + osp.sep + 'super_serial_64x64.ico')

        self.setWindowIcon(app_icon)

        #self.setGeometry(200, 200, 800, 480)
        self.resize(800, 480)

        self.super_serial_menu = QtWidgets.QMenu('&Super Serial', self)
        self.menuBar().addMenu(self.super_serial_menu)

        self.super_serial_menu.addAction('&Connect to Device', self.connect,
            QtCore.Qt.CTRL + QtCore.Qt.Key_P)

        # The function addAction returns a QAction object.
        discconect_action = self.super_serial_menu.addAction('&Disconnect', self.disconnect,
            QtCore.Qt.CTRL + QtCore.Qt.Key_D)
        discconect_action.setEnabled(False)

        self.super_serial_menu.addAction('&Set Title', self.setTitle)

        self.super_serial_menu.addAction('&Exit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.super_serial_menu)

        self.view_menu = QtWidgets.QMenu('&View', self)
        self.menuBar().addMenu(self.view_menu)

        console_action = self.view_menu.addAction('Show Console', self.showConsole,
            'Ctrl+`')

        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&Documentation', self.documentation,
            QtCore.Qt.Key_F1)
        self.help_menu.addAction('&Super Serial Webpage', self.webpage)
        self.help_menu.addAction('&About Super Serial', self.about)

        self.main_widget = QtWidgets.QWidget(self)

        l = QtWidgets.QVBoxLayout(self.main_widget)

        mono_font = QtGui.QFont('Hack')

        top = QtWidgets.QTextEdit()
        top.setCurrentFont(mono_font)
        top.setFontPointSize(12)
        top.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # self.console = QtWidgets.QTextEdit()
        self.console = ConsoleWidget()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(top)
        splitter.addWidget(self.console)

        splitter.setSizes([600, 200])

        top.append("hello world")

        l.addWidget(splitter)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.statusBar().showMessage("Nothing here yet.", 2000)
        self.console.hide()

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, 'Super Serial',
            'Super Serial\r\nVersion: {}'.format(_super_serial_version))

    def webpage(self):
        url = QUrl('http://superserial.io')
        QDesktopServices.openUrl(url)

    def documentation(self):
        url = QUrl('http://docs.superserial.io/en/latest/')
        QDesktopServices.openUrl(url)

    def connect(self):
        dialog = SerialConfigDialog()
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()

        serial_config = dialog.getSerialConfig()
        if serial_config is None:
            return

        # Connect to the serial port.
        self.serial_conn = QtSerialPort.QSerialPort

    def disconnect(self):
        pass

    def setTitle(self):
        dialog = SetTitleDialog()
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()

        new_title = dialog.getTitle()
        if new_title != '':
            self.setWindowTitle(new_title)

    def showConsole(self):
        # To make the console not viewable...
        # https://stackoverflow.com/a/371634
        if self.console.isHidden():
            self.console.show()
        else:
            self.console.hide()

    def closeEvent(self, event):
        # This method is overriding the event 'close'.

        if not preferences['prompt_on_quit']:
            return

        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Message',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class SetTitleDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SetTitleDialog, self).__init__(parent)

        self.setWindowTitle("Set Window Title")
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self._title = ''

        self.titleLineEdit = QtWidgets.QLineEdit()
        self.setTitleButton = QtWidgets.QPushButton("Set Title")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        self.setTitleButton.clicked.connect(self.setTitle)
        self.cancelButton.clicked.connect(self.cancel)

        # http://www.bogotobogo.com/Qt/Qt5_GridLayout.php
        layout = QtWidgets.QGridLayout()
        #layout.setColumnStretch(1, 1)
        layout.setColumnMinimumWidth(0, 200)
        layout.setColumnMinimumWidth(1, 100)

        # row, column, rowspan, colspan
        layout.addWidget(self.titleLineEdit, 0, 0, 1, 2)
        layout.addWidget(self.setTitleButton, 1, 0, 1, 1)
        layout.addWidget(self.cancelButton, 1, 1, 1, 1)

        self.setLayout(layout)

    def cancel(self):
        self._title = ''
        self.close()

    def setTitle(self):
        self._title = self.titleLineEdit.text()
        self.close()

    def getTitle(self):
        return self._title


class SerialConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SerialConfigDialog, self).__init__(parent)

        self.setWindowTitle('Set Window Title')
        # https://doc.qt.io/qt-5/qt.html
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.MSWindowsFixedSizeDialogHint)

        self.portLabel = QtWidgets.QLabel('Serial Port')

        self.portComboBox = QtWidgets.QComboBox()
        self.portComboBox.addItem("COM4")
        self.portComboBox.addItem("COM5")
        self.portComboBox.addItem("COM6")

        self.scanComsButton = QtWidgets.QPushButton('Scan COMs')

        self.baudrateLabel = QtWidgets.QLabel('Baudrate')

        self.baudrateEdit = QtWidgets.QLineEdit('115200')

        self.databitsLabel = QtWidgets.QLabel('Databits')

        self.databitsComboBox = QtWidgets.QComboBox()
        self.databitsComboBox.addItem('5')
        self.databitsComboBox.addItem('6')
        self.databitsComboBox.addItem('7')
        self.databitsComboBox.addItem('8')
        self.databitsComboBox.setCurrentIndex(3)

        self.stopbitsLabel = QtWidgets.QLabel('Stopbits')

        self.stopbitsComboBox = QtWidgets.QComboBox()
        self.stopbitsComboBox.addItem('1')
        self.stopbitsComboBox.addItem('1.5')
        self.stopbitsComboBox.addItem('2')
        self.stopbitsComboBox.setCurrentIndex(0)

        self.parityLabel = QtWidgets.QLabel('Parity')

        self.parityComboBox = QtWidgets.QComboBox()
        self.parityComboBox.addItem('NONE')
        self.parityComboBox.addItem('ODD')
        self.parityComboBox.addItem('EVEN')
        self.parityComboBox.addItem('SPACE')
        self.parityComboBox.addItem('MARK')
        self.parityComboBox.setCurrentIndex(0)

        self.flowControlLabel = QtWidgets.QLabel('Flow Control')

        self.flowControlComboBox = QtWidgets.QComboBox()
        self.flowControlComboBox.addItem('NONE')
        self.flowControlComboBox.addItem('XON/XOFF')
        self.flowControlComboBox.addItem('RTS/CTS')
        self.flowControlComboBox.addItem('DSR/DTR')
        self.flowControlComboBox.setCurrentIndex(2)

        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.connectButton = QtWidgets.QPushButton('Connect')
        self.saveButton = QtWidgets.QPushButton('Save')
        self.loadButton = QtWidgets.QPushButton('Load')

        self.cancelButton.clicked.connect(self.cancel)
        self.connectButton.clicked.connect(self.connect)

        # http://www.bogotobogo.com/Qt/Qt5_GridLayout.php
        layout = QtWidgets.QGridLayout()
        #layout.setColumnStretch(1, 1)
        # layout.setColumnMinimumWidth(0, 200)
        # layout.setColumnMinimumWidth(1, 100)

        # row, column, rowspan, colspan
        layout.addWidget(self.portLabel, 0, 0, 1, 2)
        layout.addWidget(self.portComboBox, 0, 2, 1, 1)
        layout.addWidget(self.scanComsButton, 0, 3, 1, 1)

        layout.addWidget(self.baudrateLabel, 1, 0, 1, 2)
        layout.addWidget(self.baudrateEdit, 1, 2, 1, 2)

        layout.addWidget(self.databitsLabel, 2, 0, 1, 2)
        layout.addWidget(self.databitsComboBox, 2, 2, 1, 2)

        layout.addWidget(self.stopbitsLabel, 3, 0, 1, 2)
        layout.addWidget(self.stopbitsComboBox, 3, 2, 1, 2)

        layout.addWidget(self.parityLabel, 4, 0, 1, 2)
        layout.addWidget(self.parityComboBox, 4, 2, 1, 2)

        layout.addWidget(self.flowControlLabel, 5, 0, 1, 2)
        layout.addWidget(self.flowControlComboBox, 5, 2, 1, 2)

        layout.addWidget(self.cancelButton, 6, 0, 1, 1)
        layout.addWidget(self.connectButton, 6, 1, 1, 1)
        layout.addWidget(self.saveButton, 6, 2, 1, 1)
        layout.addWidget(self.loadButton, 6, 3, 1, 1)

        self.setLayout(layout)

        # Set default configuration. Set to 'None' so that if the dialog is
        # canceled the system won't try to connect.
        self._serial_config = None

    def cancel(self):
        self._serial_config = None
        self.close()

    def connect(self):
        # http://pyqt.sourceforge.net/Docs/PyQt5/QtSerialPort.html#PyQt5-QtSerialPort
        # https://doc.qt.io/qt-5/qserialport.html
        serial_config = {
            'port': self.portComboBox.currentText(),
            'baudrate': int(self.baudrateEdit.text()),
            'databits': int(self.databitsComboBox.currentText()),
            'stopbits': self.stopbitsComboBox.currentText(),
            'parity': self.parityComboBox.currentText(),
            'flow_control': self.flowControlComboBox.currentText()
        }

        # Attempt to connect to the device. If not successful shake the
        # window.

        print(serial_config)

        elf._serial_config = serial_config
        self.close()

    def getSerialConfig(self):
        return _serial_config


class ConsoleWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ConsoleWidget, self).__init__(parent)

        self.consoleOutput = QtWidgets.QTextEdit()
        self.consoleInput = QtWidgets.QLineEdit()

        self.consoleOutput.setReadOnly(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.consoleOutput)
        layout.addWidget(self.consoleInput)

        self.consoleInput.returnPressed.connect(self.onEnterKey)

        self.setLayout(layout)

        self._ric = console.RemoteConsole()

    def onEnterKey(self):
        # https://github.com/pallets/werkzeug/blob/master/werkzeug/debug/console.py
        # https://www.pythoncentral.io/embed-interactive-python-interpreter-console/

        user_input = self.consoleInput.text()
        self.consoleInput.setText('')

        self._ric.push(user_input)
        output = self._ric.getResult()

        self.consoleOutput.append('>>> ' + user_input)
        self.consoleOutput.append(output[:-1])


def main():
    global app
    global preferences

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=_super_serial_version)

    args = parser.parse_args()

    # Load the preferences file.
    with open('preferences.json', encoding='utf-8') as data_file:
        contents = data_file.read()
        # Remove all comments that start with "//".
        contents = re.sub('//.*[\r\n]*', '', contents, 0, re.M)
        # Remove blank lines.
        contents = re.sub('^\s*[\r\n]*', '', contents, 0, re.M)

        preferences = json.loads(contents)

    app = QtWidgets.QApplication(sys.argv)

    script_dir = osp.dirname(osp.realpath(__file__))
    app_icon = QtGui.QIcon(script_dir + osp.sep + 'super_serial_64x64.ico')
    app.setWindowIcon(app_icon)

    aw = ApplicationWindow()
    aw.show()

    app.exec()


if __name__ == '__main__':
    main()
