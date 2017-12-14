"""
"""

import sys

from PyQt5 import QtCore, QtWidgets, QtGui

import material_colors as mc


class ColorButton(QtWidgets.QPushButton):
    def __init__(self, parent, color):
        super(ColorButton, self).__init__(parent)
        self.color = color
        self.setStyleSheet('background-color: {}; border: 1px solid white; width: 34px; height: 34px;'.format(color))

    def enterEvent(self, event):
        #self.setStyleSheet('background-color: {};'.format(self.color))
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def leaveEvent(self, event):
        #self.setStyleSheet('background-color: {}; border: none;'.format(self.color))
        self.setCursor(QtCore.Qt.ArrowCursor)


class MaterialColorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MaterialColorDialog, self).__init__(parent)
        self.setWindowTitle('Material Color Dialog')
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(380, 300)
        self.selected_color = mc.colors['blue']['400']
        # Use a grid layout for the color buttons.
        # http://doc.qt.io/qt-5/qtwidgets-widgets-calculator-example.html
        # 10 columns for the shades and then one row per color
        # The crust with nothing on it.
        btn_layout = QtWidgets.QGridLayout()
        btn_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)

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
        self.show()

    def _onColorClick(self):
        print(self.sender().color)
        self.selected_color = self.sender().color
        self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    dialog = MaterialColorDialog()
    dialog.show()
    sys.exit(app.exec_())
