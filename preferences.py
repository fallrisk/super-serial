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

import json
import os
import re

from PyQt5 import QtCore

import console

# Keep in alphabetical order.
_default_prefs = {
    'font_face': 'Operator Mono',
    'font_size': 11,
    'prompt_on_quit': False
}

_watcher = QtCore.QFileSystemWatcher()

class PreferencesManager(QtCore.QObject):

    prefsUpdated = QtCore.pyqtSignal()

    def __init__(self):
        super(PreferencesManager, self).__init__()
        global _default_prefs
        global _watcher
        _watcher.fileChanged.connect(self._onFileChanged)
        self._preferences = _default_prefs
        self._file_path = None

    def parseFileJson(self, file_path):
        # Load the preferences file if it exists.
        with open(file_path, encoding='utf-8') as data_file:
            contents = data_file.read()
            # Remove all comments that start with "//".
            contents = re.sub('//.*[\r\n]*', '', contents, 0, re.M)
            # Remove blank lines.
            contents = re.sub('^\s*[\r\n]*', '', contents, 0, re.M)
            # Parse the file as JSON.
            self._preferences = json.loads(contents)

    def load(self, file_path):
        if not os.path.isfile(file_path):
            console.enqueue('Could not find preferences file "{}". Using default preferences.'.format(
                file_path))
            return

        try:
            self.parseFileJson(file_path)
        except TypeError:
            # If there was a parsing error keep the current settings and
            # post a message to the console.
            console.enqueue('Error parsing the preferences file.')
        global _watcher
        _watcher.addPath(file_path)
        self._file_path = file_path

    def _onFileChanged(self, file_path):
        """

        Parameters
        ----------
        file_path
            The path to the file that was just updated/modified.
        """
        print('File was updated!')
        self.load(self._file_path)
        print('Finished updating prefs.')
        self.prefsUpdated.emit()

    def get(self, pref_name):
        return self._preferences[pref_name]


_preferences_manager = PreferencesManager()


def load(file_path):
    global _preferences_manager
    _preferences_manager.load(file_path)


def subscribe(subscriber):
    global _preferences_manager
    _preferences_manager.prefsUpdated.connect(subscriber)


def get(pref_name):
    global _preferences_manager
    return _preferences_manager.get(pref_name)
