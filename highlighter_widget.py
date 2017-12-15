"""

"""

import sys

from PyQt5 import QtCore, QtWidgets, QtGui

import material_color_widget as mcw
import material_colors as mc
import preferences


class SmallButton(QtWidgets.QPushButton):
    def __init__(self, text, tip_text, parent=None, checkable=False, checked_tip_text=None):
        super(SmallButton, self).__init__(text)
        self.tip_text = tip_text
        self.checked_tip_text = checked_tip_text
        self.setCheckable(checkable)
        self.text = text
        self.setToolTip(text)
        self.toggled.connect(self._onToggle)

    def _onToggle(self, checked):
        if checked:
            if self.checked_tip_text is not None:
                self.setToolTip(self.checked_tip_text)
        else:
            self.setToolTip(self.tip_text)

    def sizeHint(self):
        return QtCore.QSize(32, 26)


class HighlighterWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, config=None):
        super(HighlighterWidget, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()

        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)

        if config is None:
            self._config = {
                'color': mc.blue['400'],
                'case_sensitive': False,
                'regex': 'FW',
                'enabled': True
            }
        else:
            self._config = config

        self.__color_button = SmallButton('', 'Select highlight color.')
        self.__color_button.clicked.connect(self._onColorButtonClick)
        self.__case_sensitive_button = SmallButton('Bb', 'Make case sensitive.',
            None, True, 'Make case insensitive.')
        self.__regex_line_edit = QtWidgets.QLineEdit()
        self.__regex_line_edit.setMinimumHeight(26)
        self.__regex_line_edit.setPlaceholderText('Regular Expresssion')
        self.__enable_button = SmallButton('', 'Enable highlighter',
            None, True, 'Disable highlighter.')

        layout.addWidget(self.__color_button)
        layout.addWidget(self.__case_sensitive_button)
        layout.addWidget(self.__regex_line_edit)
        layout.addWidget(self.__enable_button)

        self.applyConfig(self._config)

        self.setLayout(layout)

    def applyConfig(self, config):
        # TODO: Check the config for the correct keys. If it doesn't have the
        # correct keys then throw an exception.

        self.__color_button.setStyleSheet(
            'background-color: {}; border: none;'.format(config['color']))
        if config['enabled']:
            self.__enable_button.setChecked(True)
        else:
            self.__enable_button.setChecked(False)
        if config['case_sensitive']:
            self.__case_sensitive_button.setChecked(True)
        else:
            self.__case_sensitive_button.setChecked(False)
        self.__regex_line_edit.setText(config['regex'])
        self._config = config


    def _onColorButtonClick(self):
        dialog = mcw.MaterialColorDialog(self.parent())
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
        self.__color_button.setStyleSheet('background-color: {}; border: none;'.format(dialog.selected_color))
        self._config['color'] = dialog.selected_color

    def _onCaseSensitiveBtnClick(self):
        pass

    def _onEnabledBtnClick(self):
        pass

    def get_highlight_config(self):
        self._config['regex'] = self.__regex_line_edit.text()
        return self._config


class HighlighterManagerWidget(QtWidgets.QWidget):
    pass


def show_highlighter_widget():
    app = QtWidgets.QApplication(sys.argv)
    hw = HighlighterWidget()
    hw.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    show_highlighter_widget()
