
import sys

from PyQt5 import QtCore, QtWidgets, QtGui

import material_colors as mc

class MaterialColorDialog(QtWidgets.QDialog):
	def __init__(self, parent=None):
		super(MaterialColorDialog, self).__init__(parent)
		self.setWindowTitle('Material Color Dialog')
		# Use a grid layout for the color buttons.
		# http://doc.qt.io/qt-5/qtwidgets-widgets-calculator-example.html


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = FindDialog()
    dialog.show()
    sys.exit(app.exec_())
