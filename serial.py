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

import queue
import threading
import time

from PyQt5 import QtCore, QtSerialPort

#import console

class SerialPort(QtCore.QObject):
    """

    """

    # https://doc.qt.io/qt-5/qserialport.html
    qt_errors = [
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
    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()

    def __init__(self):
        super(SerialPort, self).__init__()
        self._serial_conn = QtSerialPort.QSerialPort()
        # Create a thread for serial port reading and writing.
        #self._serial_rwthread = threading.Thread()
        # Hold the value of config errors.
        self._config_error = ''
        # The dictionary used for successful configuration.
        self._serial_config = None
        self.is_connected = False
        self._end_thread = False

    def __del__(self):
        self.close()

    def connect(self):
        """Connects to a serial port.

        Returns
        -------
        Returns True if the connection was made successfully. False if there was an error.
        """
        # Connect to the device.
        open_result = self._serial_conn.open(QtCore.QIODevice.ReadWrite)
        print('open_result', open_result)

        if not open_result:
            return self._serial_conn.error()

        # Check for errors connecting to the device.

        # Start reading and writing in the thread.
        self._end_thread = False
        self._serial_rwthread = threading.Thread(target=self._run)
        self._serial_rwthread.start()

        # Indicate we have a new connection.
        #console.log('Connected to device.')
        self.connected.emit()
        self.is_connected = True
        return 0

    def close(self):
        if self.is_connected:
            self._serial_conn.close()
            self.disconnected.emit()
            self.is_connected = False
            self._end_thread = True
            self._serial_rwthread.join()

    def set_config(self, config):
        """
        Attempts to set the configuration for a QSerialPort from a dictionary
        configuration. If any of the items can't be converted to a QSerialPort
        configuration item then False is returned.

        https://doc.qt.io/qt-5/qserialport.html

        """
        # Clear the configuration error.
        self._config_error = ''

        self._serial_conn.setPortName(config['port'])
        self._serial_conn.setBaudRate(config['baudrate'], QtSerialPort.QSerialPort.AllDirections)

        if config['stopbits'] == '1':
            self._serial_conn.setStopBits(QtSerialPort.QSerialPort.OneStop)
        elif config['stopbits'] == '1.5':
            self._serial_conn.setStopBits(QtSerialPort.QSerialPort.OneAndHalfStop)
        elif config['stopbits'] == '2':
            self._serial_conn.setStopBits(QtSerialPort.QSerialPort.TwoStop)
        else:
            self._config_error = 'Invalid choice for stop bits.'
            return False

        if config['databits'] == 5:
            self._serial_conn.setDataBits(QtSerialPort.QSerialPort.Data5)
        elif config['databits'] == 6:
            self._serial_conn.setDataBits(QtSerialPort.QSerialPort.Data6)
        elif config['databits'] == 7:
            self._serial_conn.setDataBits(QtSerialPort.QSerialPort.Data7)
        elif config['databits'] == 8:
            self._serial_conn.setDataBits(QtSerialPort.QSerialPort.Data8)
        else:
            self._config_error = 'Invalid choice for data bits.'

        if config['parity'] == 'NONE':
            self._serial_conn.setParity(QtSerialPort.QSerialPort.NoParity)
        elif config['parity'] == 'ODD':
            self._serial_conn.setParity(QtSerialPort.QSerialPort.NoParity)
        elif config['parity'] == 'EVEN':
            self._serial_conn.setParity(QtSerialPort.QSerialPort.NoParity)
        elif config['parity'] == 'SPACE':
            self._serial_conn.setParity(QtSerialPort.QSerialPort.NoParity)
        elif config['parity'] == 'MARK':
            self._serial_conn.setParity(QtSerialPort.QSerialPort.NoParity)
        else:
            self._config_error = 'Invalid choice for parity.'

        if config['flow_control'] == 'NONE':
            self._serial_conn.setFlowControl(QtSerialPort.QSerialPort.NoFlowControl)
        elif config['flow_control'] == 'XON/XOFF':
            self._serial_conn.setFlowControl(QtSerialPort.QSerialPort.SoftwareControl)
        elif config['flow_control'] == 'RTS/CTS':
            self._serial_conn.setFlowControl(QtSerialPort.QSerialPort.HardwareControl)
        else:
            self._config_error = 'Invalid choice for flow control.'

        self._serial_config = config

        return True

    def config_to_str(self):
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
        s += ' ' + str(c['baudrate'])
        s += ' ' + str(c['databits'])
        s += ' ' + c['stopbits']

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
            s += ' Unk'

        if c['flow_control'] == 'NONE':
            s += ' None'
        elif c['flow_control'] == 'XON/XOFF':
            s += ' XON/XOFF'
        elif c['flow_control'] == 'RTS/CTS':
            s += ' RTS/CTS'
        else:
            s += ' Unk;'

        return s

    def get_config_error(self):
        return self._config_error

    def _run(self):
        buf = QtCore.QByteArray()
        while not self._end_thread:
            time.sleep(1.0)
            available = self._serial_conn.bytesAvailable()
            print('available', available)
            if  available > 0:
                data = self._serial_conn.read(available)
                print('data', len(data), data)

    def _scan_coms(self):
        """Scan for available com ports.
        """

        # http://doc.qt.io/qt-5/qserialportinfo.html#availablePorts
        #QSerialPortInfo()
        pass


