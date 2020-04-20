# -*- coding: cp1251 -*-
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from lib4db import abstractModel, calcT
from PyQt5 import uic

class dCalcAdiabatic(QDialog):
    def __init__(self, parent=None, item=None):
        super(QDialog, self).__init__(parent)
        uic.loadUi('dCalcAdiabatic.ui', self)
        self.item=item
        pr=item.parent().child(0).data(0, 100)
        for p in pr:
            if p[0] in [u'Плотность', 'rho']:
                self.eRho.setText(p[1].split()[0])
            if p[0] in [u'Терлоемкость', u'Удельная теплоемкость', 'C', 'Cp']:
                self.eCp.setText(p[1].split()[0])         

    def accept(self):
        beta=float(self.eBeta.text())
        rho=float(self.eRho.text())
        cp=float(self.eCp.text())
        b=beta/rho/cp
        n=self.item.childCount()
        
        for i in range(n):
            d=self.item.child(i).data(0,100)
            if d.type in ['c', 't', 's']:
                calcT(d, b)
                self.parent().log.appendPlainText('{0}: Tmax={1:.1f}'.format(self.item.child(i).text(0),max(d['T'])))
#        for e in self.parent().exps:
#            e.calcT(b)
        self.done(1) 