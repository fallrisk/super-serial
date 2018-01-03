"""
Copyright 2017-2018 Justin Watson

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

from code import InteractiveConsole
import sys

from PyQt5 import QtCore


class SimpleStream:
    def __init__(self):
        self.reset()

    def reset(self):
        self.out = []

    def write(self,line):
        self.out.append(line)

    def flush(self):
        output = '\n'.join(self.out)
        self.reset()
        return output


class RemoteConsole(InteractiveConsole):
    def __init__(self):
        self.stdout = sys.stdout
        self.internal_out = SimpleStream()
        InteractiveConsole.__init__(self)
        self._result = ''

    def get_output(self):
        sys.stdout = self.internal_out

    def return_output(self):
        sys.stdout = self.stdout

    def push(self,line):
        self._result = ''

        # Wrap the execution around a seperate stream.
        self.get_output()
        InteractiveConsole.push(self,line)
        self.return_output()

        output = self.internal_out.flush()

        if self._result == '':
            self._result = output

        return

    def write(self, data):
        self._result = data

    def getResult(self):
        return self._result


# The following is a singleton for handling console messages.
# Any QtObject can use these functions to pass messages to the console.
# This removes having to pass the console object into every object, widget,
# function, etc.
#
# https://stackoverflow.com/a/6760821
#

class ConsoleMsgHandler(QtCore.QObject):

    _messages = []

    newMsg = QtCore.pyqtSignal()

    def enqueue(self, msg):
        self._messages.append(msg)
        self.newMsg.emit()

    def dequeue(self):
        return self._messages.pop(0)


messages = ConsoleMsgHandler()


def enqueue(msg):
    global messages
    messages.enqueue(msg)


def dequeue():
    global messages
    return messages.dequeue()
