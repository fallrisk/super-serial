
from code import InteractiveConsole
import sys

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
        self._result = 'exception:' + data

    def getResult(self):
        return self._result

