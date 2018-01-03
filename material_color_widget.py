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

import sys

from PyQt5 import QtCore, QtWidgets, QtGui

import material_colors as mc


class ColorButton(QtWidgets.QPushButton):
    def __init__(self, parent, color):
        super(ColorButton, self).__init__(parent)
        self.color = color
        self.setStyleSheet('background-color: {}; border: none; width: 34px; height: 34px;'.format(color))

    def enterEvent(self, event):
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def leaveEvent(self, event):
        self.setCursor(QtCore.Qt.ArrowCursor)


class MaterialColorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MaterialColorDialog, self).__init__(parent)
        self.setWindowTitle('Material Color Dialog')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(370, 300)
        self.selected_color = mc.colors['blue']['400']
        # Use a grid layout for the color buttons.
        # http://doc.qt.io/qt-5/qtwidgets-widgets-calculator-example.html
        # 10 columns for the shades and then one row per color
        # The crust with nothing on it.
        btn_layout = QtWidgets.QGridLayout()
        btn_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(1)

        color_buttons = []
        r = c = 0
        for name, shades in mc.colors.items():
            for n, shade in shades.items():
                # Skip the 'A' shades.
                if n in ['A100', 'A200', 'A400', 'A700']:
                    continue
                b = ColorButton(self, shade)
                b.clicked.connect(self._onColorClick)
                color_buttons.append(b)
                # Add widget params. are: row, column, rowspan, colspan.
                btn_layout.addWidget(b, r, c, 1, 1)
                c += 1
            r += 1
            c = 0

        scroll_area_content = QtWidgets.QWidget()
        scroll_area_content.setLayout(btn_layout)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_area_content)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def _onColorClick(self):
        self.selected_color = self.sender().color
        self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    dialog = MaterialColorDialog()
    dialog.show()
    sys.exit(app.exec_())
