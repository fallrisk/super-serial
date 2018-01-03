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

from copy import deepcopy

from PyQt5 import QtCore, QtWidgets, QtGui

import material_colors as mc

class HighlightManager(QtCore.QObject):
    def __init__(self, num_highlights=10):
        self._highlights = []
        highlight_config = {
            'color': mc.blue['400'],
            'case_sensitive': False,
            'pattern': '',
            'enabled': False
        }

        color_names = list(mc.colors.keys())
        for x in range(num_highlights):
            highlight_config['color'] = mc.colors[color_names[x]]['400']
            self._highlights.append(deepcopy(highlight_config))

    def get_highlights(self):
        """
        Returns the highlights as a list.
        """
        return deepcopy(self._highlights)

    def set_highlight(self, index, config):
        self._highlights[index] = config
