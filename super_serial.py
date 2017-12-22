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
import json
import os
import os.path as osp
import re
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
# Semantic Versioning https://semver.org/
# At the very least the patch number always increases per build/release.
__version__ = 'v0.1.0' # Major.Minor.Patch


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, args):
        QtWidgets.QMainWindow.__init__(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Super Serial")


        # Initialization Pre UI
        # ---------------------
        # Only things that HAVE to be done before the UI go here.
        script_dir = osp.dirname(osp.realpath(__file__))

        # Set the application icon.
        app_icon = QtGui.QIcon(script_dir + osp.sep + 'super_serial_64x64.ico')
        self.setWindowIcon(app_icon)

        # Create file watcher for the preferences file.
        self._watcher = QtCore.QFileSystemWatcher()
        preferences.setWatcher(self._watcher)

        serial_config = None
        if args.port is not None:
            serial_config = serial_args_to_config(args)

        self._serialPort = serial.SerialPort()
        self._highlighManager = highlighter.HighlightManager()

        # Widgets
        # -------
        self._mainWidget = QtWidgets.QWidget(self)
        self._consoleWidget = ConsoleWidget()
        self._serialConfigDialog = SerialConfigDialog(self, self._serialPort)
        self._connectionLabel = QtWidgets.QLabel('Disconnected')
        self._serialConsoleWidget = serial_console_widget.SerialConsoleWidget(
            self._highlighManager, self)
        self._serialConsoleWidget.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self._highlightManagerWidget = highlighter_widget.HighlightManagerWidget(
            self, self._highlighManager)

        # Menu
        # ----
        self.superSerialMenu = QtWidgets.QMenu('&Super Serial', self)
        self.viewMenu = QtWidgets.QMenu('&View', self)
        self.helpMenu = QtWidgets.QMenu('&Help', self)

        self.menuBar().addMenu(self.superSerialMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.helpMenu)

        # Menu: Super Serial
        # ------------------
        self.connectAction = self.superSerialMenu.addAction(
            '&Connect to Device', self.connect,
            QtCore.Qt.CTRL + QtCore.Qt.Key_P)
        self.disconnectAction = self.superSerialMenu.addAction('&Disconnect',
            self.disconnect, QtCore.Qt.CTRL + QtCore.Qt.Key_D)
        self.disconnectAction.setEnabled(False)
        self.superSerialMenu.addAction('&Set Title', self.setTitle)
        self.superSerialMenu.addAction('&Exit', self.close,
            QtCore.Qt.CTRL + QtCore.Qt.Key_Q)

        # Menu: View
        # ----------
        self.consoleAction = self.viewMenu.addAction(
            'Show Console', self.showConsole, 'Ctrl+`')
        self.highlightManagerAction = self.viewMenu.addAction(
            'Show Highlights', self.showHighlightManager)
        self.viewMenu.addSeparator()
        self.localEchoAction = self.viewMenu.addAction('Enable Local Echo',
            self._onLocalEchoAction)
        self.localEchoAction.setCheckable(True)
        self.localEchoAction.setChecked(False)
        # self.show_crlf_action = self.viewMenu.addAction('Show CR and LF',
        #     self._onShowCrLfAction)

        # Menu: Help
        self.helpMenu.addAction('&Documentation', self.documentation,
            QtCore.Qt.Key_F1)
        self.helpMenu.addAction('&Super Serial Webpage', self.webpage)
        self.helpMenu.addAction('&About Super Serial', self.about)

        # Connections
        # -----------
        console.messages.newMsg.connect(self._onNewConsoleMsg)
        # Subscribe to preferences file update events.
        preferences.subscribe(self._onPrefsUpdate)
        self._serialPort.opened.connect(self._onSerialOpened)
        self._serialPort.closed.connect(self._onSerialClosed)
        self._serialPort.readyRead.connect(self._onSerialPortReadyRead)
        self._serialConsoleWidget.dataWrite.connect(self._onSerConWidWrite)

        # Layout
        # ------
        layout = QtWidgets.QVBoxLayout(self._mainWidget)
        # Remove the space outlining the widgets.
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.statusBar().addWidget(self._connectionLabel)

        self._splitter.addWidget(self._serialConsoleWidget)
        self._splitter.addWidget(self._consoleWidget)
        self._splitter.setSizes([500, 300])

        layout.addWidget(self._splitter)

        self._mainWidget.setFocus()
        self.setCentralWidget(self._mainWidget)
        self._consoleWidget.hide()
        self.resize(800, 480)

        # Initialization Post UI
        # ----------------------
        console.enqueue('Version: {}'.format(__version__))
        console.enqueue('Executable Path: {}'.format(osp.realpath(__file__)))
        console.enqueue('Working Directory: {}'.format(os.getcwd()))

        with open('style.qss', encoding='utf-8') as style_file:
            self.setStyleSheet(style_file.read())

        # Load preferences file.
        preferences_file = os.getcwd() + osp.sep + 'preferences.json'
        if args.preferences_file is not None:
            preferences_file = args.preferences_file
        preferences.load(preferences_file)
        console.enqueue('Loaded preferences file: {}'.format(preferences_file))

        mono_font = QtGui.QFont(preferences.get('font_face'))
        mono_font.setPointSize(int(preferences.get('font_size')))
        self._consoleWidget.setFont(mono_font)
        self._serialConsoleWidget.document().setDefaultFont(mono_font)

        # Load connections file.
        self.connections_file = os.getcwd() + osp.sep + 'connections.json'
        if args.connections_file is not None:
            self.connections_file = args.connections_file

        self._connections = {}
        self._connections_successfully_loaded = False
        connections = serial.SerialConnections.load(self.connections_file)
        connections_okay = serial.SerialConnections.check(connections)
        # If the connections configuration checked out okay then load the
        # connections. Otherwise don't load them.
        if connections_okay:
            # Convert the connections into a dict using the names.
            # This is so we can find the items by name quickly.
            # https://docs.python.org/3.6/faq/design.html#how-are-dictionaries-implemented
            d = {}
            for c in connections:
                d[c['name']] = c
                d[c['name']]['stop_bits'] = float(d[c['name']]['stop_bits'])
            self._serialConfigDialog.setConnections(d)
            self._connections = d
            self._connections_successfully_loaded = True
            console.enqueue('Connections file loaded: {}'.format(
                self.connections_file))

        if serial_config is not None:
            config_result = self._serial_port.setConfig(serial_config)
            if not config_result:
                console.enqueue('Error serial config.')
            else:
                open_result = self._serial_port.open()
                if open_result != 0:
                    console.enqueue('Error connection: {}'.format(
                        self._serial_port.qserialport_errors[config_result]))
        self._serialConfigDialog.updatePortList()

    def about(self):
        QtWidgets.QMessageBox.about(self, 'Super Serial',
            'Copyright 2017 Justin Watson\r\nSuper Serial\r\nVersion: {}'.
            format(__version__))

    def closeEvent(self, event):
        # This method is overriding the event 'close'.
        if self._connections_successfully_loaded:
            serial.SerialConnections.save(list(self._connections.values()),
                self.connections_file)

        if not preferences.get('prompt_on_quit'):
            return

        quit_msg = "Are you sure you want to exit Super Serial?"
        reply = QtWidgets.QMessageBox.question(self, 'Message',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
        self.fileQuit()

    def connect(self):
        self._serialConfigDialog.setModal(True)
        self._serialConfigDialog.show()

    def disconnect(self):
        self._serial_port.close()

    def documentation(self):
        url = QUrl('http://docs.superserial.io/en/latest/')
        QDesktopServices.openUrl(url)

    def setTitle(self):
        # Memory Leaks with Dialogs https://stackoverflow.com/a/37928086.
        dialog = SetTitleDialog(self)
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
        self._serialConfigDialog.close()
        self.close()

    def showConsole(self):
        # To make the console not viewable...
        # https://stackoverflow.com/a/371634
        if self._consoleWidget.isHidden():
            self._consoleWidget.show()
            self.consoleAction.setText('Hide Console')
        else:
            self._consoleWidget.hide()
            self.consoleAction.setText('Show Console')

    def showHighlightManager(self):
        self._highlightManagerWidget.show()

    def webpage(self):
        url = QUrl('http://superserial.io')
        QDesktopServices.openUrl(url)

    def _onLocalEchoAction(self):
        if self._serialConsoleWidget.local_echo_enabled:
            self._serialConsoleWidget.local_echo_enabled = False
            self.localEchoAction.setChecked(False)
        else:
            self._serialConsoleWidget.local_echo_enabled = True
            self.localEchoAction.setChecked(True)

    def _onNewConsoleMsg(self):
        self._consoleWidget.consoleOutput.append(console.dequeue())

    def _onPrefsUpdate(self):
        mono_font = QtGui.QFont(preferences.get('font_face'))
        mono_font.setPointSize(int(preferences.get('font_size')))
        self._consoleWidget.setFont(mono_font)
        self._serialConsoleWidget.document().setDefaultFont(mono_font)

    def _onSerialClosed(self):
        self.connectionLabel.setText('Disconnected')
        self.disconnectAction.setEnabled(False)
        self.connectAction.setEnabled(True)

    def _onSerialOpened(self):
        self.connectionLabel.setText('Connected: ' + self._serialPort.configToStr())
        self.disconnectAction.setEnabled(True)
        self.connectAction.setEnabled(False)
        self._serialConsoleWidget.setFocus(QtCore.Qt.OtherFocusReason)

    def _onSerialPortReadyRead(self):
        available = self._serialPort.bytesAvailable()
        if available > 0:
            data = self._serialPort.read(available)
            self._serialConsoleWidget.putData(data.decode('utf-8'))

    def _onSerConWidWrite(self, data):
        """
        on serial console widget write
        """
        b = data.encode('ascii')
        if self._serialPort.is_connected:
            self._serialPort.write(b)

    def _onShowCrLfAction(self):
        if self._serialConsoleWidget.show_crlf:
            self._serialConsoleWidget.show_crlf = False
            self._showCrLfAction.setText('Hide CR and LF')
        else:
            self._serialConsoleWidget.show_crlf = True
            self.showCrLfAction.setText('Show CR and LF')
        self._serialConsoleWidget.repaint()


class SetTitleDialog(QtWidgets.QDialog):
    """Dialog to prompt the user for a name for the application window.
    """

    def __init__(self, parent=None):
        super(SetTitleDialog, self).__init__(parent)

        self.setWindowTitle("Set Window Title")
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.Dialog)

        # Widgets
        # -------
        self.titleLineEdit = QtWidgets.QLineEdit()
        self.setTitleButton = QtWidgets.QPushButton("Set Title")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        # Connections
        # -----------
        self.setTitleButton.clicked.connect(self._onSetTitle)
        self.cancelButton.clicked.connect(self._onCancel)

        # Layout
        # ------
        # http://www.bogotobogo.com/Qt/Qt5_GridLayout.php
        layout = QtWidgets.QGridLayout()

        # row, column, rowspan, colspan
        layout.addWidget(self.titleLineEdit, 0, 0, 1, 2)
        layout.addWidget(self.setTitleButton, 1, 0, 1, 1)
        layout.addWidget(self.cancelButton, 1, 1, 1, 1)

        self.setLayout(layout)
        self.adjustSize()

    def _onCancel(self):
        self.close()

    def _onSetTitle(self):
        self.parentWidget().setWindowTitle(self.titleLineEdit.text())
        self.close()


class ConnectionListWidget(QtWidgets.QWidget):
    """Displays connections and allows the user to load and save them.

    TODO JKW: On mouse over of an item show more detailed information
    about the connection off to the right.
    """

    itemDoubleClicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(ConnectionListWidget, self).__init__(parent)

        self.itemWidgets = []
        self._connections = []

        # Widgets
        # -------
        self.listWidget = QtWidgets.QListWidget()
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.renameButton = QtWidgets.QPushButton('Rename')
        self.loadButton = QtWidgets.QPushButton('Load')

        # Connections
        # -----------
        self.listWidget.itemDoubleClicked.connect(self._onItemDoubleClicked)

        # Layout
        # ------
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addWidget(self.renameButton)
        self.buttonLayout.addWidget(self.loadButton)
        self.mainLayout.addWidget(self.listWidget)
        self.mainLayout.addLayout(self.buttonLayout)
        self.setLayout(self.mainLayout)

    def setConnections(self, connections):
        """Sets the connections in the list to those provided by the
        parameter "connections".
        """
        self.listWidget.clear()
        for name, c in connections.items():
            self.itemWidgets.append(QtWidgets.QListWidgetItem(name,
                self.listWidget))
        self._connections = connections

    def getConnections(self):
        return self._connections

    def getCurrentConfig(self):
        """
        Returns
        -------
        Returns the currently selected connection.
        """
        return self._connections[self.listWidget.currentItem().text()]

    def _onItemDoubleClicked(self):
        self.itemDoubleClicked.emit()


class SerialConfigWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SerialConfigWidget, self).__init__(parent)

        # Widgets
        # -------
        self.nameLabel = QtWidgets.QLabel('Name (for saving)')
        self.nameEdit = QtWidgets.QLineEdit('')

        self.portLabel = QtWidgets.QLabel('Serial Port')
        self.portComboBox = QtWidgets.QComboBox()
        self.portComboBox.setCurrentIndex(3)
        self.portComboBox.setEditable(True)

        self.scanComsButton = QtWidgets.QPushButton('Scan COMs')

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

        # Connections
        # -----------

        # Layout
        # ------
        # http://www.bogotobogo.com/Qt/Qt5_GridLayout.php
        connectionLayout = QtWidgets.QGridLayout()

        # row, column, rowspan, colspan
        connectionLayout.addWidget(self.nameLabel, 0, 0, 1, 2)
        connectionLayout.addWidget(self.nameEdit, 0, 2, 1, 2)

        connectionLayout.addWidget(self.portLabel, 1, 0, 1, 2)
        connectionLayout.addWidget(self.portComboBox, 1, 2, 1, 1)
        connectionLayout.addWidget(self.scanComsButton, 1, 3, 1, 1)

        connectionLayout.addWidget(self.baudrateLabel, 2, 0, 1, 2)
        connectionLayout.addWidget(self.baudrateEdit, 2, 2, 1, 2)

        connectionLayout.addWidget(self.databitsLabel, 3, 0, 1, 2)
        connectionLayout.addWidget(self.databitsComboBox, 3, 2, 1, 2)

        connectionLayout.addWidget(self.stopbitsLabel, 4, 0, 1, 2)
        connectionLayout.addWidget(self.stopbitsComboBox, 4, 2, 1, 2)

        connectionLayout.addWidget(self.parityLabel, 5, 0, 1, 2)
        connectionLayout.addWidget(self.parityComboBox, 5, 2, 1, 2)

        connectionLayout.addWidget(self.flowControlLabel, 6, 0, 1, 2)
        connectionLayout.addWidget(self.flowControlComboBox, 6, 2, 1, 2)

        connectionLayout.addWidget(self.errorWidget, 7, 0, 1, 4)

        connectionLayout.addWidget(self.cancelButton, 8, 0, 1, 1)
        connectionLayout.addWidget(self.connectButton, 8, 1, 1, 1)
        connectionLayout.addWidget(self.saveButton, 8, 2, 1, 1)
        connectionLayout.addWidget(self.loadButton, 8, 3, 1, 1)

        self.setLayout(connectionLayout)

    def updatePortList(self, ports):
        """
        Set the combo-box to the provided list.

        Parameters
        ----------
        ports : str
            List of port names that are available.
        """
        if len(ports) > 0:
            self.portComboBox.clear()
            for port in ports:
                self.portComboBox.addItem(port)

    def getCurrentConfig(self):
        """Gets the current configuration from the UI elements and returns
        a dictionary of the config.
        """
        serial_config = {
            'name': self.nameEdit.text(),
            'port': self.portComboBox.currentText(),
            'baud': int(self.baudrateEdit.text()),
            'data_bits': int(self.databitsComboBox.currentText()),
            'stop_bits': float(self.stopbitsComboBox.currentText()),
            'parity': self.parityComboBox.currentText(),
            'flow_control': 'none',
            'local_echo_enabled': False
        }

        if self.flowControlComboBox.currentText() == 'RTS/CTS':
            serial_config['flow_control'] = 'hardware'
        else:
            serial_config['flow_control'] = 'software'


        return serial_config


class SerialConfigDialog(QtWidgets.QDialog):
    """Dialog to configure the serial port.
    """

    def __init__(self, parent=None, serialPort=None):
        """
        Parameters
        -----------
        serialPort : serial.SerialPort
            The serial port.
        """
        super(SerialConfigDialog, self).__init__(parent)
        self.setObjectName('serialConfigDialog')

        if serialPort is None:
            raise Exception('Serial port cannot be None on SerialConfigDialog')
        self._serialPort = serialPort

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('Serial Configuration')
        # https://doc.qt.io/qt-5/qt.html
        # http://doc.qt.io/qt-5/qt.html#WindowType-enum
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint)

        # Widgets
        # -------
        self._serialConfigWidget = SerialConfigWidget(self)
        self._connectionListWidget = ConnectionListWidget(self)

        # Connections
        # -----------
        self._serialConfigWidget.loadButton.clicked.connect(
            self._showConnectionsWidget)
        self._serialConfigWidget.cancelButton.clicked.connect(self._onCancel)
        self._serialConfigWidget.connectButton.clicked.connect(self._onConnect)
        self._serialConfigWidget.scanComsButton.clicked.connect(
            self.updatePortList)
        self._serialConfigWidget.saveButton.clicked.connect(self._onSave)

        self._connectionListWidget.cancelButton.clicked.connect(
            self._showSerialConfigWidget)
        self._connectionListWidget.loadButton.clicked.connect(
            self._onLoadConnection)
        self._connectionListWidget.itemDoubleClicked.connect(
            self._onLoadConnection)

        # Layout
        # ------
        self._stackedLayout = QtWidgets.QStackedLayout(self)
        self._stackedLayout.addWidget(self._serialConfigWidget)
        self._stackedLayout.addWidget(self._connectionListWidget)
        self._stackedLayout.setCurrentIndex(0)
        self.setLayout(self._stackedLayout)
        self.adjustSize()

    def applyConfig(self, config):
        """Applies a serial connection configuration to the connection UI.
        """
        scw = self._serialConfigWidget

        scw.nameEdit.setText(config['name'])
        scw.portComboBox.setEditText(config['port'])
        scw.baudrateEdit.setText(str(config['baud']))
        scw.databitsComboBox.setCurrentIndex(
            scw.databitsComboBox.findText(str(config['data_bits'])))
        # If the stop bits is a whole number remove the ".0" from the string.
        if config['stop_bits'] % 1 == 0.0:
            sb = str(config['stop_bits'])[:-2]
            scw.stopbitsComboBox.setCurrentIndex(
                scw.stopbitsComboBox.findText(sb))
        else:
            scw.stopbitsComboBox.setCurrentIndex(
                scw.stopbitsComboBox.findText(str(config['stop_bits'])))
        scw.parityComboBox.setCurrentIndex(
            scw.parityComboBox.findText(str(config['parity']).upper()))
        if config['flow_control'] == 'none':
            scw.flowControlComboBox.setCurrentIndex(0)
        elif config['flow_control'] == 'hardware':
            scw.flowControlComboBox.setCurrentIndex(1)
        else:
            scw.flowControlComboBox.setCurrentIndex(2)

    def saveCurrentConfig(self):
        """Saves the current configuration.
        """
        config = self._serialConfigWidget.getCurrentConfig()
        # Check for a name.
        if config['name'] == '':
            self._serialConfigWidget.errorWidget.setText(
                'You need a name if you want to save.')
            self._shake()
            return
        connections = self._connectionListWidget.getConnections()
        connections[config['name']] = config
        self._connectionListWidget.setConnections(connections)

    def setConnections(self, connections):
        """Applies the connections list to the serial configuration widget.
        """
        self._connectionListWidget.setConnections(connections)

    def updatePortList(self):
        """Updates the list of ports. Uses the Qt library to get the available
        ports.
        """
        serialInfos = self._serialPort.scanComs()
        availablePorts = []
        for info in serialInfos:
            availablePorts.append(info.portName())
        self._serialConfigWidget.updatePortList(availablePorts)

    def _onCancel(self):
        self.hide()

    def _onConnect(self):
        scw = self._serialConfigWidget
        serial_config = self._serialConfigWidget.getCurrentConfig()
        config_result = self._serialPort.setConfig(serial_config)

        if not config_result:
            self._shake()
            scw.errorWidget.setText(self._serialPort.get_config_error())
            return

        open_result = self._serialPort.open()

        if open_result != 0:
            self._shake()
            scw.errorWidget.setText(
                self._serialPort.qserialport_errors[open_result])
            return

        self.hide()

    def _onLoadConnection(self):
        """Called when the user clicks the load button in the connection list
        window. This will grab the currently selected configuration and apply
        it to the current settings and change the view.
        """
        config = self._connectionListWidget.getCurrentConfig()
        self.applyConfig(config)
        self._showSerialConfigWidget()

    def _onSave(self):
        """Save the current configuration.
        """
        self.saveCurrentConfig()

    def _shake(self):
        """Shakes the window. Like shaking your head as in "no", there was
        a problem.
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

    def _showConnectionsWidget(self):
        """Shows the connections list UI.
        """
        self._stackedLayout.setCurrentIndex(1)

    def _showSerialConfigWidget(self):
        """Shows the serial configuration UI.
        """
        self._stackedLayout.setCurrentIndex(0)


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
    parser.add_argument('--connections', dest='connections_file', help='Specify a connections file instead of the default.')
    parser.add_argument('--data-bits', type=int, dest='data_bits', default=8, help='Number of data bits. Default 8')
    parser.add_argument('--fc', '--flow-control', dest='flow_control', default='n', help='Hardware RTS/CTS (h), Software XON/XOFF (s), or None (n). Default \'n\' for None')
    parser.add_argument('--parity', dest='parity', default='n', help='Parity of the connection. None (n), Odd (o), Even (e), Space (s), Mark (m). Default \'n\' for None')
    parser.add_argument('--port', dest='port', help='Port to connect to at start.')
    parser.add_argument('--preferences', dest='preferences_file', help='Specify a preferences file instead of the default.')
    parser.add_argument('--stop-bits', dest='stop_bits', type=float, default=1, help='Number of stop bits. Default 1')
    parser.add_argument('--version', action='version', version=__version__)

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    script_dir = osp.dirname(osp.realpath(__file__))
    app_icon = QtGui.QIcon(script_dir + osp.sep + 'super_serial_64x64.ico')
    app.setWindowIcon(app_icon)

    aw = ApplicationWindow(args)
    aw.show()

    app.exec_()

    # Check for memory leaks.
    # https://stackoverflow.com/a/37928086
    print('\n'.join(repr(w) for w in app.allWidgets()))


if __name__ == '__main__':
    main()
