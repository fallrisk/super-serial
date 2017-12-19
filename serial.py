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

from datetime import datetime
import queue
import threading
import time

from PyQt5 import QtCore, QtSerialPort

import console

class SerialPort(QtSerialPort.QSerialPort):

    # https://doc.qt.io/qt-5/qserialport.html
    qserialport_errors = [
        'No error occurred.',
        'An error occurred while attemptiong to open a non-existing device.',
        'An error occurred while attempting to open an already opened device by another process or a user not having enough permission and credentials to open.',
        'An error occurred while attempting to open an already opened device in this object.',
        'Parity error detected by the hardware while reading data. This value is obsolete. We strongly advise against using it in new code.',
        'Framing error detected by the hardware while reading data. This value is obsolete. We strongly advise against using it in new code.',
        'Break condition detected by the hardware on the input line. This value is obsolete. We strongly advise against using it in new code.',
        'An I/O error occurred while writing the data.',
        'An I/O error occurred while reading the data.',
        'An I/O error occurred when a resource becomes unavailable, e.g. when the device is unexpectedly removed from the system.',
        'The requested device operation is not supported or prohibited by the running operating system.'<
        'An unidentified error occurred.',
        'A timeout error occurred. This value was introduced in QtSerialPort 5.2.',
        'This error occurs when an operation is executed that can only be successfully performed if the device is open. This value was introduced in QtSerialPort 5.2.'
    ]

    # Signal to indicate a new connection has been made.
    opened = QtCore.pyqtSignal()
    closed = QtCore.pyqtSignal()

    def __init__(self):
        super(QtSerialPort.QSerialPort, self).__init__()
        # Hold the value of config errors.
        self._config_error = ''
        # The dictionary used for successful configuration.
        self._serial_config = None
        self.is_connected = False

    def open(self):
        """Connects to a serial port.

        Returns
        -------
        Returns True if the connection was made successfully. False if there was an error.
        """
        # Connect to the device.
        open_result = super(SerialPort, self).open(QtCore.QIODevice.ReadWrite)

        if not open_result:
            return self.error()

        # Indicate we have a new connection.
        self.opened.emit()
        self.is_connected = True
        console.enqueue('Connected to device {} at {:%d %b. %Y %H:%M:%S}.'.format(
            self._serial_config['port'], datetime.now()))
        return 0

    def close(self):
        super(SerialPort, self).close()
        console.enqueue('Disconnected from device {} at {:%d %b. %Y %H:%M:%S}.'.format(
            self._serial_config['port'], datetime.now()))
        self.is_connected = False
        self.closed.emit()

    def setConfig(self, config):
        """
        Attempts to set the configuration for a QSerialPort from a dictionary
        configuration. If any of the items can't be converted to a QSerialPort
        configuration item then False is returned.

        https://doc.qt.io/qt-5/qserialport.html

        """
        # Clear the configuration error.
        self._config_error = ''

        self.setPortName(config['port'])
        self.setBaudRate(config['baud'], QtSerialPort.QSerialPort.AllDirections)

        if config['stop_bits'] == '1':
            self.setStopBits(QtSerialPort.QSerialPort.OneStop)
        elif config['stop_bits'] == '1.5':
            self.setStopBits(QtSerialPort.QSerialPort.OneAndHalfStop)
        elif config['stop_bits'] == '2':
            self.setStopBits(QtSerialPort.QSerialPort.TwoStop)
        else:
            self._config_error = 'Invalid choice for stop bits.'
            return False

        if config['data_bits'] == 5:
            self.setDataBits(QtSerialPort.QSerialPort.Data5)
        elif config['data_bits'] == 6:
            self.setDataBits(QtSerialPort.QSerialPort.Data6)
        elif config['data_bits'] == 7:
            self.setDataBits(QtSerialPort.QSerialPort.Data7)
        elif config['data_bits'] == 8:
            self.setDataBits(QtSerialPort.QSerialPort.Data8)
        else:
            self._config_error = 'Invalid choice for data bits.'

        if config['parity'] == 'NONE':
            self.setParity(QtSerialPort.QSerialPort.NoParity)
        elif config['parity'] == 'ODD':
            self.setParity(QtSerialPort.QSerialPort.NoParity)
        elif config['parity'] == 'EVEN':
            self.setParity(QtSerialPort.QSerialPort.NoParity)
        elif config['parity'] == 'SPACE':
            self.setParity(QtSerialPort.QSerialPort.NoParity)
        elif config['parity'] == 'MARK':
            self.setParity(QtSerialPort.QSerialPort.NoParity)
        else:
            self._config_error = 'Invalid choice for parity.'

        if config['flow_control'] == 'NONE':
            self.setFlowControl(QtSerialPort.QSerialPort.NoFlowControl)
        elif config['flow_control'] == 'XON/XOFF':
            self.setFlowControl(QtSerialPort.QSerialPort.SoftwareControl)
        elif config['flow_control'] == 'RTS/CTS':
            self.setFlowControl(QtSerialPort.QSerialPort.HardwareControl)
        else:
            self._config_error = 'Invalid choice for flow control.'

        self._serial_config = config

        return True

    def configToStr(self):
        """Makes a string version of the serial configuration.

        Form
        ----
        comport baudrate databits stopsbits parity flowcontrol

        e.g.
        COM4 115200 8 1 None RTS/CTS
        """

        if self._serial_config is None:
            return ''

        c = self._serial_config
        s = c['port']
        s += ' ' + str(c['baud'])
        s += ' ' + str(c['data_bits'])
        s += ' ' + c['stop_bits']

        if c['parity'] == 'NONE':
            s += ' None'
        elif c['parity'] == 'ODD':
            s += ' Odd'
        elif c['parity'] == 'EVEN':
            s += ' Even'
        elif c['parity'] == 'SPACE':
            s += ' Space'
        elif c['parity'] == 'MARK':
            s += ' Mark'
        else:
            s += ' Unk' # Unknown

        if c['flow_control'] == 'NONE':
            s += ' None'
        elif c['flow_control'] == 'XON/XOFF':
            s += ' XON/XOFF'
        elif c['flow_control'] == 'RTS/CTS':
            s += ' RTS/CTS'
        else:
            s += ' Unk' # Unknown

        return s

    def scanComs(self):
        # http://doc.qt.io/qt-5/qserialportinfo.html#availablePorts
        available_ports = QtSerialPort.QSerialPortInfo.availablePorts()
        return available_ports
