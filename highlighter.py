"""

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
