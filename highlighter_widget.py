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

    def enterEvent(self, event):
        self.setCursor(QtCore.Qt.PointingHandCursor)
        super(SmallButton, self).enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(QtCore.Qt.ArrowCursor)
        super(SmallButton, self).leaveEvent(event)

    def sizeHint(self):
        return QtCore.QSize(32, 26)


class HighlighterWidget(QtWidgets.QWidget):

    updated = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, config=None, index=0):
        super(HighlighterWidget, self).__init__(parent)
        self.index = index
        layout = QtWidgets.QHBoxLayout()

        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)

        if config is None:
            self._config = {
                'color': mc.blue['400'],
                'case_sensitive': False,
                'pattern': 'FW',
                'enabled': True
            }
        else:
            self._config = config

        self.__color_button = mcw.ColorButton(self, self._config['color'])
        self.__color_button.clicked.connect(self._onColorButtonClick)
        self.__case_sensitive_button = SmallButton('Bb', 'Make case sensitive.',
            None, True, 'Make case insensitive.')
        self.__regex_line_edit = QtWidgets.QLineEdit()
        self.__regex_line_edit.setMinimumHeight(24)
        self.__regex_line_edit.setPlaceholderText('Regular Expresssion')
        self.__regex_line_edit.textChanged.connect(self._onRegexChanged)
        self.__enable_button = SmallButton('', 'Enable highlighter',
            None, True, 'Disable highlighter.')
        self.__enable_button.clicked.connect(self._onEnabledBtnClick)

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
            'background-color: {};'.format(config['color']))
        if config['enabled']:
            self.__enable_button.setChecked(True)
        else:
            self.__enable_button.setChecked(False)
        if config['case_sensitive']:
            self.__case_sensitive_button.setChecked(True)
        else:
            self.__case_sensitive_button.setChecked(False)
        self.__regex_line_edit.setText(config['pattern'])
        self._config = config

    def _onColorButtonClick(self):
        dialog = mcw.MaterialColorDialog()
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
        self.__color_button.setStyleSheet('background-color: {};'.format(dialog.selected_color))
        self._config['color'] = dialog.selected_color
        self.updated.emit(self.index)

    def _onCaseSensitiveBtnClick(self):
        if self.__case_sensitive_button.isChecked():
            self._config['case_sensitive'] = True
        else:
            self._config['case_sensitive'] = True
        self.updated.emit(self.index)

    def _onEnabledBtnClick(self):
        if self.__enable_button.isChecked():
            self._config['enabled'] = True
        else:
            self._config['enabled'] = False
        self.updated.emit(self.index)

    def _onRegexChanged(self):
        self._config['pattern'] = self.__regex_line_edit.text()
        self.updated.emit(self.index)

    def get_highlight_config(self):
        self._config['pattern'] = self.__regex_line_edit.text()
        return self._config


class HighlightManagerWidget(QtWidgets.QDialog):
    def __init__(self, parent, highlight_manager):
        super(HighlightManagerWidget, self).__init__(parent)

        self.highlight_manager = highlight_manager

        self.setWindowTitle('Highlight Manager')
        layout = QtWidgets.QVBoxLayout()

        self._highlighter_widgets = []
        for i, highlight in enumerate(highlight_manager.get_highlights()):
            hw = HighlighterWidget(self, None, i)
            hw.applyConfig(highlight)
            hw.updated.connect(self._onHighlightWidgetUpdate)
            self._highlighter_widgets.append(hw)
            layout.addWidget(hw)

        self.setLayout(layout)

    def _onHighlightWidgetUpdate(self, widget_index):
        self.highlight_manager.set_highlight(widget_index,
            self._highlighter_widgets[widget_index].get_highlight_config())


def show_highlighter_widget():
    app = QtWidgets.QApplication(sys.argv)
    hw = HighlighterWidget()
    hw.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    show_highlighter_widget()
