# -*- coding: cp1251 -*-
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic

class dAddExperiment(QDialog):
    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)
        uic.loadUi('addExperiment.ui', self)
        self.cbEditDE.stateChanged.connect(self.enableEditDE)
        self.cbTemp.stateChanged.connect(self.enableTemp)
        self.cbExpType.currentIndexChanged.connect(self.cbIndexChanged)

    def enableEditDE(self, state):
        self.leMeanDE.setEnabled(state==2)
    
    def enableTemp(self, state):
        self.leT0.setEnabled(state==2)

    def cbIndexChanged(self, index):
        if index==3:
            self.label_2.setText(u'Показатель напряженного состояния')
        else:
            self.label_2.setText(u'Средняя скорость деформации')
