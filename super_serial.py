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

References
----------
* http://pyqt.sourceforge.net/Docs/PyQt5/modules.html#ref-module-index
* https://doc.qt.io/qt-5/qt.html
* http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html
* https://wiki.python.org/moin/PyQt/Threading%2C_Signals_and_Slots
* https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting
* http://pyqt.sourceforge.net/Docs/PyQt5/signals_slots.html
* https://wiki.python.org/moin/PyQt/SampleCode
* https://www.mail-archive.com/pyqt@riverbankcomputing.com/msg16050.html

"""

import argparse
import copy
import os
import os.path as osp
import sys

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.Qt import QDesktopServices, QUrl

import console
import highlighter
import highlighter_widget
import preferences
import serial
import serial_console_widget

# http://pyqt.sourceforge.net/Docs/PyQt5/gotchas.html#crashes-on-exit
app = None

__author__ = 'Justin Watson'
__version__ = 'v0.1.0'

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, args):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Super Serial")

        self.consoleWidget = ConsoleWidget()
        console.messages.newMsg.connect(self._onNewConsoleMsg)

        self._watcher = QtCore.QFileSystemWatcher()
        preferences.setWatcher(self._watcher)

        preferenes_file = os.getcwd() + osp.sep + 'preferences.json'
        if args.preferences is not None:
            preferenes_file = args.preferences
        preferences.load(preferenes_file)

        serial_config = None
        if args.port is not None:
            serial_config = serial_args_to_config(args)

        console.enqueue('Version: {}'.format(__version__))
        console.enqueue('Executable Path: {}'.format(osp.realpath(__file__)))
        console.enqueue('Working Directory: {}'.format(os.getcwd()))
        console.enqueue('Loaded preferences file: {}'.format(preferenes_file))

        # Subscribe to preferences file update events.
        preferences.subscribe(self._onPrefsUpdate)
        # preferences.prefsUpdated.connect(self._onPrefsUpdate)

        # The serial port class manages all the serial port.
        # It creates a thread to hold the data. It handles
        # connecting and sending events to the gui.
        self._serial_port = serial.SerialPort()

        script_dir = osp.dirname(osp.realpath(__file__))
        app_icon = QtGui.QIcon(script_dir + osp.sep + 'super_serial_64x64.ico')

        self.setWindowIcon(app_icon)

        #self.setGeometry(200, 200, 800, 480)
        self.resize(800, 480)

        with open('style.qss', encoding='utf-8') as style_file:
            self.setStyleSheet(style_file.read())

        self.super_serial_menu = QtWidgets.QMenu('&Super Serial', self)
        self.menuBar().addMenu(self.super_serial_menu)

        self.connect_action = self.super_serial_menu.addAction('&Connect to Device', self.connect,
            QtCore.Qt.CTRL + QtCore.Qt.Key_P)

        # The function addAction returns a QAction object.
        self.disconnect_action = self.super_serial_menu.addAction('&Disconnect', self.disconnect,
            QtCore.Qt.CTRL + QtCore.Qt.Key_D)
        self.disconnect_action.setEnabled(False)

        self.super_serial_menu.addAction('&Set Title', self.setTitle)

        self.super_serial_menu.addAction('&Exit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.super_serial_menu)

        self.view_menu = QtWidgets.QMenu('&View', self)
        self.menuBar().addMenu(self.view_menu)

        self.console_action = self.view_menu.addAction('Show Console', self.showConsole,
            'Ctrl+`')
        self.highlighter_manager_action = self.view_menu.addAction('Show Highlights', self.showHighlights)

        self.view_menu.addSeparator()
        self.local_echo_action = self.view_menu.addAction('Enable Local Echo', self._onLocalEchoAction)
        self.local_echo_action.setCheckable(True)
        self.local_echo_action.setChecked(False)

        self.show_crlf_action = self.view_menu.addAction('Show CR and LF', self._onShowCrLfAction)

        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&Documentation', self.documentation,
            QtCore.Qt.Key_F1)
        self.help_menu.addAction('&Super Serial Webpage', self.webpage)
        self.help_menu.addAction('&About Super Serial', self.about)

        self.main_widget = QtWidgets.QWidget(self)

        l = QtWidgets.QVBoxLayout(self.main_widget)
        # Remove the space outlining the widgets.
        l.setContentsMargins(0, 0, 0, 0)

        mono_font = QtGui.QFont(preferences.get('font_face'))
        mono_font.setPointSize(int(preferences.get('font_size')))

        self.consoleWidget.setFont(mono_font)

        self.highlight_manager = highlighter.HighlightManager()

        self.serialConsoleWidget = serial_console_widget.SerialConsoleWidget(self.highlight_manager, self)
        self.serialConsoleWidget.document().setDefaultFont(mono_font)
        self.serialConsoleWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.highlightManagerWidget = highlighter_widget.HighlightManagerWidget(self, self.highlight_manager)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(self.serialConsoleWidget)
        splitter.addWidget(self.consoleWidget)

        splitter.setSizes([500, 300])

        l.addWidget(splitter)
        l.setSpacing(0)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.connectionLabel = QtWidgets.QLabel('Disconnected')

        self.statusBar().addWidget(self.connectionLabel)
        self.consoleWidget.hide()

        self._serial_port.opened.connect(self._onSerialOpened)
        self._serial_port.closed.connect(self._onSerialClosed)
        self._serial_port.readyRead.connect(self._onSerialPortReadyRead)

        self.serialConsoleWidget.dataWrite.connect(self._onSerConWidWrite)

        # Register the control character text object.
        controlCharInterface = serial_console_widget.ControlCharObject(self)
        self.serialConsoleWidget.document().documentLayout().registerHandler(
            serial_console_widget.ControlCharFormat, controlCharInterface)

        if serial_config is not None:
            config_result = self._serial_port.setConfig(serial_config)
            if not config_result:
                console.enqueue('Error serial config.')
            else:
                open_result = self._serial_port.open()
                if open_result != 0:
                    console.enqueue('Error connection: {}'.format(
                        self._serial_port.qserialport_errors[config_result]))

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, 'Super Serial',
            'Copyright 2017 Justin Watson\r\nSuper Serial\r\nVersion: {}'.format(__version__))

    def webpage(self):
        url = QUrl('http://superserial.io')
        QDesktopServices.openUrl(url)

    def documentation(self):
        url = QUrl('http://docs.superserial.io/en/latest/')
        QDesktopServices.openUrl(url)

    def connect(self):
        dialog = SerialConfigDialog(self, self._serial_port)
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()

    def disconnect(self):
        self._serial_port.close()

    def setTitle(self):
        dialog = SetTitleDialog(self)
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()

    def showConsole(self):
        # To make the console not viewable...
        # https://stackoverflow.com/a/371634
        if self.consoleWidget.isHidden():
            self.consoleWidget.show()
            self.console_action.setText('Hide Console')
        else:
            self.consoleWidget.hide()
            self.console_action.setText('Show Console')

    def showHighlights(self):
        self.highlightManagerWidget.show()

    def _onShowCrLfAction(self):
        if self.serialConsoleWidget.show_crlf:
            self.serialConsoleWidget.show_crlf = False
            self.show_crlf_action.setText('Hide CR and LF')
        else:
            self.serialConsoleWidget.show_crlf = True
            self.show_crlf_action.setText('Show CR and LF')
        self.serialConsoleWidget.repaint()

    def _onLocalEchoAction(self):
        if self.serialConsoleWidget.local_echo_enabled:
            self.serialConsoleWidget.local_echo_enabled = False
            self.local_echo_action.setChecked(False)
        else:
            self.serialConsoleWidget.local_echo_enabled = True
            self.local_echo_action.setChecked(True)

    def closeEvent(self, event):
        # This method is overriding the event 'close'.

        if not preferences.get('prompt_on_quit'):
            return

        quit_msg = "Are you sure you want to exit Super Serial?"
        reply = QtWidgets.QMessageBox.question(self, 'Message',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def _onSerialOpened(self):
        self.connectionLabel.setText('Connected: ' + self._serial_port.configToStr())
        self.disconnect_action.setEnabled(True)
        self.connect_action.setEnabled(False)
        self.serialConsoleWidget.setFocus(QtCore.Qt.OtherFocusReason)

    def _onSerialClosed(self):
        self.connectionLabel.setText('Disconnected')
        self.disconnect_action.setEnabled(False)
        self.connect_action.setEnabled(True)

    def _onSerConWidWrite(self, data):
        """
        on serial console widget write
        """
        b = data.encode('ascii')
        if self._serial_port.is_connected:
            self._serial_port.write(b)

    def _onSerialPortReadyRead(self):
        available = self._serial_port.bytesAvailable()
        if available > 0:
            data = self._serial_port.read(available)
            self.serialConsoleWidget.putData(data.decode('utf-8'))

    def _onNewConsoleMsg(self):
        self.consoleWidget.consoleOutput.append(console.dequeue())

    def _onPrefsUpdate(self):
        mono_font = QtGui.QFont(preferences.get('font_face'))
        mono_font.setPointSize(int(preferences.get('font_size')))
        self.consoleWidget.setFont(mono_font)
        self.serialConsoleWidget.document().setDefaultFont(mono_font)



class SetTitleDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SetTitleDialog, self).__init__(parent)

        self.setWindowTitle("Set Window Title")
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog)

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
        self.adjustSize()

    def cancel(self):
        self.close()

    def setTitle(self):
        self.parentWidget().setWindowTitle(self.titleLineEdit.text())
        self.close()


class SerialConfigDialog(QtWidgets.QDialog):
    """Dialog to configure the serial port.

    Parameters
    -----------
    serial_port
        serial.SerialPort instance

    """
    def __init__(self, parent, serial_port=None):
        super(SerialConfigDialog, self).__init__(parent)
        # Memory Leaks with Dialogs https://stackoverflow.com/a/37928086
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self._serial_port = serial_port
        self.setWindowTitle('Set Window Title')
        # https://doc.qt.io/qt-5/qt.html
        # http://doc.qt.io/qt-5/qt.html#WindowType-enum
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint )

        self.portLabel = QtWidgets.QLabel('Serial Port')

        self.portComboBox = QtWidgets.QComboBox()
        self.portComboBox.setCurrentIndex(3)
        self.portComboBox.setEditable(True)

        available_ports = self._serial_port.scanComs()
        if len(available_ports) > 0:
            self.portComboBox.clear()
            for port in available_ports:
                self.portComboBox.addItem(port.portName())

        self.scanComsButton = QtWidgets.QPushButton('Scan COMs')
        self.scanComsButton.clicked.connect(self._onScanComs)

        self.baudrateLabel = QtWidgets.QLabel('Baud')

        self.baudrateEdit = QtWidgets.QLineEdit('115200')

        self.databitsLabel = QtWidgets.QLabel('Data bits')

        self.databitsComboBox = QtWidgets.QComboBox()
        self.databitsComboBox.addItem('5')
        self.databitsComboBox.addItem('6')
        self.databitsComboBox.addItem('7')
        self.databitsComboBox.addItem('8')
        self.databitsComboBox.setCurrentIndex(3)

        self.stopbitsLabel = QtWidgets.QLabel('Stop bits')

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
        self.flowControlComboBox.addItem('RTS/CTS')
        self.flowControlComboBox.addItem('XON/XOFF')
        self.flowControlComboBox.setCurrentIndex(1)

        self.errorWidget = QtWidgets.QLabel()
        self.errorWidget.setObjectName('error')
        self.errorWidget.setWordWrap(True)

        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.connectButton = QtWidgets.QPushButton('Connect')
        self.saveButton = QtWidgets.QPushButton('Save')
        self.loadButton = QtWidgets.QPushButton('Load')

        self.cancelButton.clicked.connect(self._onCancel)
        self.connectButton.clicked.connect(self._onConnect)

        # http://www.bogotobogo.com/Qt/Qt5_GridLayout.php
        layout = QtWidgets.QGridLayout()

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

        layout.addWidget(self.errorWidget, 6, 0, 1, 4)

        layout.addWidget(self.cancelButton, 7, 0, 1, 1)
        layout.addWidget(self.connectButton, 7, 1, 1, 1)
        layout.addWidget(self.saveButton, 7, 2, 1, 1)
        layout.addWidget(self.loadButton, 7, 3, 1, 1)

        self.setLayout(layout)
        self.adjustSize()

    def _onCancel(self):
        self.close()

    def _onConnect(self):
        serial_config = {
            'port': self.portComboBox.currentText(),
            'baud': int(self.baudrateEdit.text()),
            'data_bits': int(self.databitsComboBox.currentText()),
            'stop_bits': self.stopbitsComboBox.currentText(),
            'parity': self.parityComboBox.currentText(),
            'flow_control': self.flowControlComboBox.currentText()
        }

        config_result = self._serial_port.setConfig(serial_config)

        if not config_result:
            self._shake()
            self.errorWidget.setText(self._serial_port.get_config_error())
            return

        open_result = self._serial_port.open()

        if open_result != 0:
            self._shake()
            self.errorWidget.setText(
                self._serial_port.qserialport_errors[open_result])
            return

        self.close()

    def _onScanComs(self):
        available_ports = self._serial_port.scanComs()
        if len(available_ports) > 0:
            self.portComboBox.clear()
            for port in available_ports:
                self.portComboBox.addItem(port.portName())


    def _shake(self):
        """Shakes the window. Like shaking your head as in there was a problem.
        """
        self.shakeAnimation = QtCore.QSequentialAnimationGroup()

        current_geometry = self.geometry()

        move_geometry = copy.deepcopy(current_geometry)
        move_geometry.translate(-10, 0)
        animation0 = QtCore.QPropertyAnimation(self, bytearray('geometry', 'ASCII'))
        animation0.setDuration(40)
        animation0.setStartValue(current_geometry)
        animation0.setEndValue(move_geometry)
        self.shakeAnimation.addAnimation(animation0)

        move_geometry.translate(20, 0)
        animation1 = QtCore.QPropertyAnimation(self, bytearray('geometry', 'ASCII'))
        animation1.setDuration(40)
        animation1.setStartValue(current_geometry)
        animation1.setEndValue(move_geometry)
        self.shakeAnimation.addAnimation(animation1)

        move_geometry.translate(-20, 0)
        animation2 = QtCore.QPropertyAnimation(self, bytearray('geometry', 'ASCII'))
        animation2.setDuration(40)
        animation2.setStartValue(current_geometry)
        animation2.setEndValue(move_geometry)
        self.shakeAnimation.addAnimation(animation2)

        move_geometry.translate(20, 0)
        animation3 = QtCore.QPropertyAnimation(self, bytearray('geometry', 'ASCII'))
        animation3.setDuration(40)
        animation3.setStartValue(current_geometry)
        animation3.setEndValue(move_geometry)
        self.shakeAnimation.addAnimation(animation3)

        move_geometry.translate(-10, 0)
        animation4 = QtCore.QPropertyAnimation(self, bytearray('geometry', 'ASCII'))
        animation4.setDuration(40)
        animation4.setStartValue(current_geometry)
        animation4.setEndValue(move_geometry)
        self.shakeAnimation.addAnimation(animation4)

        self.shakeAnimation.start()



class ConsoleWidget(QtWidgets.QWidget):
    """
    This is a console for the application as a whole. Not for the serial port.
    """
    def __init__(self, parent=None):
        super(ConsoleWidget, self).__init__(parent)

        self.consoleOutput = QtWidgets.QTextEdit()
        self.consoleInput = QtWidgets.QLineEdit()

        self.consoleOutput.setWordWrapMode(QtGui.QTextOption.NoWrap)

        self.consoleOutput.setReadOnly(True)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.consoleOutput)
        layout.addWidget(self.consoleInput)

        self.consoleInput.returnPressed.connect(self.onEnterKey)

        self.setLayout(layout)

        self._ric = console.RemoteConsole()

    def onEnterKey(self):
        # https://github.com/pallets/werkzeug/blob/master/werkzeug/debug/console.py
        # https://www.pythoncentral.io/embed-interactive-python-interpreter-console/
        # http://code.activestate.com/recipes/355319-using-codeinteractiveconsole-to-embed-a-python-she/

        user_input = self.consoleInput.text()
        self.consoleInput.setText('')

        self._ric.push(user_input)
        output = self._ric.getResult()

        self.consoleOutput.append('>>> ' + user_input)
        self.consoleOutput.append(output[:-1])

    def setFont(self, font):
        self.consoleOutput.setFont(font)
        self.consoleInput.setFont(font)


def serial_args_to_config(args):
    """
    Converts the arguments from the command line to the configuration needed
    for the class serial.SerialPort to make a connection.
    """
    if args.port is None:
        return None
    serial_config = {}
    serial_config['port'] = args.port
    serial_config['baud'] = args.baud
    serial_config['data_bits'] = args.data_bits
    serial_config['stop_bits'] = str(args.stop_bits)

    if args.parity == 'n':
        serial_config['parity'] = 'NONE'
    elif args.parity == 'o':
        serial_config['parity'] = 'ODD'
    elif args.parity == 'e':
        serial_config['parity'] = 'EVEN'
    elif args.parity == 's':
        serial_config['parity'] = 'SPACE'
    elif args.parity == 'm':
        serial_config['parity'] = 'MARK'
    else:
        serial_config['data_bits'] = 'UNK' # Unknown

    if args.flow_control == 's':
        serial_config['flow_control'] = 'XON/XOFF'
    elif args.flow_control == 'h':
        serial_config['flow_control'] = 'RTS/CTS'
    elif args.flow_control == 'n':
        serial_config['flow_control'] = 'NONE'
    else:
        serial_config['flow_control'] = 'UNK'

    return serial_config


def main():
    global app

    parser = argparse.ArgumentParser()
    parser.add_argument('--baud', type=int, dest='baud', default=115200, help='Baud of the connection. Default 115200')
    parser.add_argument('--data-bits', type=int, dest='data_bits', default=8, help='Number of data bits. Default 8')
    parser.add_argument('--fc', '--flow-control', dest='flow_control', default='n', help='Hardware RTS/CTS (h), Software XON/XOFF (s), or None (n). Default \'n\' for None')
    parser.add_argument('--parity', dest='parity', default='n', help='Parity of the connection. None (n), Odd (o), Even (e), Space (s), Mark (m). Default \'n\' for None')
    parser.add_argument('--port', dest='port', help='Port to connect to at start.')
    parser.add_argument('--preferences', help='Specify a preferences file instead of the default.')
    parser.add_argument('--stop-bits', dest='stop_bits', type=float, default=1, help='Number of stop bits. Default 1')
    parser.add_argument('--version', action='version', version=__version__)

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    script_dir = osp.dirname(osp.realpath(__file__))
    app_icon = QtGui.QIcon(script_dir + osp.sep + 'super_serial_64x64.ico')
    app.setWindowIcon(app_icon)

    aw = ApplicationWindow(args)
    aw.show()

    app.exec()


if __name__ == '__main__':
    main()
