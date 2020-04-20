# -*- coding: cp1251 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic

class dTextInput(QDialog):
    def __init__(self, parent=None, item=None):
        super(QDialog, self).__init__(parent)
        uic.loadUi('dTextInput.ui', self)
        self.item=item
        self.initForm()
        
    def initForm(self):
        self.ptComment.setPlainText(self.item.data(0,100))
