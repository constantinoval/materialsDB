from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import globalConstants as gl
from importlib import reload

class dialogShowTable(QDialog):
    def __init__(self, parent=None, item=None):
        super(QDialog, self).__init__(parent)
        uic.loadUi('tableView.ui', self)
        self.updateTable()

    def updateTable(self):
        pass

    def accept(self):
        self.done(1)

    def reject(self):
        self.done(0)


    def addRow(self, row):
        self.tableWidget.insertRow(row)
