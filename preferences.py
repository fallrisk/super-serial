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

Attributes
----------
_preferences_manager
    This was created at the module level to be a singleton. A module is only
    loaded once in Python. Regardless of the number of "import" statements
    calling it.

"""

import os
import re

from PyQt5 import QtCore
import yaml

import console

# Keep in alphabetical order.
_default_prefs = {
    'font_face': 'Operator Mono',
    'font_size': 11,
    'prompt_on_quit': False
}


class PreferencesManager(QtCore.QObject):
    """
    Class to manage preferences and subscribers. It was created as a QObject
    subclass to utilize the signals and slots asynchronous system. This allows
    updating properties of Qt widgets, such as the font.

    You must create a watcher so that the preferences file can be watched for
    live changes. A QFileSystemWatcher must be made in a QtApplication. If
    you don't you will get the error:
        QFileSystemWatcher: Removable drive notification will not work if there is no QCoreApplication instance.
    You should create the QFileSystemWatcher in your QMainWindow and set it
    with the function setWatcher.

    You should use the module level functions to interact with the preferences
    system.

    In every widget that you want to have the preferences reload on file change
    you must add a callback to the prefsUpdated signal.
    e.g. preferences.subscribe(self._onPrefsUpdate)
    Then in your callback you apply the prefrences to your widgets or systems.
    e.g.
    ```
    def _onPrefsUpdate(self):
        mono_font = QtGui.QFont(preferences.get('font_face'))
        mono_font.setPointSize(int(preferences.get('font_size')))
        self.consoleWidget.setFont(mono_font)
        self.serialConsoleWidget.document().setDefaultFont(mono_font)
    ```

    The above function takes the new font_face and font_size and applies
    them to the widgets.
    """
    prefsUpdated = QtCore.pyqtSignal()

    def __init__(self, default_prefs):
        super(PreferencesManager, self).__init__()
        self._preferences = default_prefs
        self._file_path = None
        self._watcher = None

    def parseFileYaml(self, file_path):
        # Load the preferences file if it exists.
        with open(file_path, encoding='utf-8') as data_file:
            contents = data_file.read()
            # Remove all comments that start with "//".
            #contents = re.sub('//.*[\r\n]*', '', contents, 0, re.M)
            # Remove blank lines.
            #contents = re.sub('^\s*[\r\n]*', '', contents, 0, re.M)
            # Parse the file as YAML.
            self._preferences = yaml.load(contents)

    def load(self, file_path):
        if self._watcher is None:
            raise Exception('Can\'t load preferences file until a watcher has been set.')
        if not os.path.isfile(file_path):
            console.enqueue('Could not find preferences file "{}". Using default preferences.'.format(
                file_path))
            return
        try:
            self.parseFileYaml(file_path)
        except TypeError:
            # If there was a parsing error keep the current settings and
            # post a message to the console.
            console.enqueue('Error parsing the preferences file.')
        self._watcher.addPath(file_path)
        self._file_path = file_path

    def _onFileChanged(self, file_path):
        """

        Parameters
        ----------
        file_path
            The path to the file that was just updated/modified.
        """
        self.load(self._file_path)
        self.prefsUpdated.emit()

    def setWatcher(self, watcher):
        self._watcher = watcher
        self._watcher.fileChanged.connect(self._onFileChanged)

    def get(self, pref_name):
        return self._preferences[pref_name]


_preferences_manager = PreferencesManager(_default_prefs)


def setWatcher(watcher):
    global _preferences_manager
    _preferences_manager.setWatcher(watcher)


def load(file_path):
    global _preferences_manager
    _preferences_manager.load(file_path)


def subscribe(subscriber):
    global _preferences_manager
    _preferences_manager.prefsUpdated.connect(subscriber)


def get(pref_name):
    global _preferences_manager
    return _preferences_manager.get(pref_name)
