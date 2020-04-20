# -*- coding: cp1251 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic

class dMplSetup(QDialog):
    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)
        uic.loadUi('dMplSetup.ui', self)
        self.initForm()

    def initForm(self):
        self.cbMatName.setChecked(self.parent().conf['showMaterialNameInLegend'])
        self.cbShowErrorBars.setChecked(self.parent().conf['showErrorBars'])
        self.leXLabel.setText(self.parent().conf['xlabel'])
        self.leYLabel.setText(self.parent().conf['ylabel'])
        self.cbShowLegend.setChecked(self.parent().conf['showLegend'])
        self.cbShowGrid.setChecked(self.parent().conf['showGrid'])
        self.cbFixedAxisLabels.setChecked(self.parent().conf['fixedAxisLabels'])
        self.cbLogScale.setChecked(self.parent().conf.get('xscale', 'linear')=='log')
        self.cbLine.setChecked('-' in self.parent().conf['ls'])
        self.cbMarker.setChecked('o' in self.parent().conf['ls'])
        self.leLineWidth.setValue(self.parent().conf['lw'])
        self.leMarkerSize.setValue(self.parent().conf['ms'])
        if not self.parent().exps:
            return
        exp=self.parent().exps[0]
        self.cbXaxis.addItems(exp.data.keys())
        self.cbYaxis.addItems(exp.data.keys())
        self.cbXaxis.setCurrentIndex(self.parent().conf['xaxis'])
        self.cbYaxis.setCurrentIndex(self.parent().conf['yaxis'])
        self.cbXautoscale.setChecked(self.parent().conf['autox'])
        self.cbYautoscale.setChecked(self.parent().conf['autoy'])
        self.leXmin.setText(str(self.parent().conf['xbound'][0]))
        self.leXmax.setText(str(self.parent().conf['xbound'][1]))
        self.leYmin.setText(str(self.parent().conf['ybound'][0]))
        self.leYmax.setText(str(self.parent().conf['ybound'][1]))

