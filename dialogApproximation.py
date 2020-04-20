# -*- coding: cp1251 -*-
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from lib4db import *
from PyQt5 import uic
from copy import deepcopy
import globalConstants as gl
from importlib import reload

class dDataApproximation(QDialog):
    def __init__(self, parent=None, item=None):
        reload(gl)
        super(QDialog, self).__init__(parent)
        uic.loadUi('dialogApproximation.ui', self)
        self.lines=[]
        self.item=item
        self.bApplyForm.clicked.connect(self.updateForm)
        self.tParameters.setColumnCount(5)
        self.tParameters.setHorizontalHeaderLabels(['Parameter', 'Value', 'Vary', 'min', 'max'])
        self.bCalculateParameters.clicked.connect(self.calculateParameters)
        et=self.parent().exps[0].type
        if et=='t':
            et='c'
        self.cbApproximationForm.addItems(self.parent().models.get(et,['{A}+{B}*x1']))
        self.et=et
        self.approximation=0
        self.bRedraw.clicked.connect(self.redraw)
        self.updateForm()
        for i, k in enumerate(self.approximation.expParams):
            v=gl.varSymbols[k]
            s=('x_{%i}' % (i+1)) + '-'+v
            p=QPixmap()
            p.loadFromData(renderFormula(s, dpi=100, fontsize=10, convertFormula=False))
            l=QLabel()
            l.setPixmap(p)
            self.hlVariables.addWidget(l)
        self.cbApproximationForm.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.cbApproximationForm.setDuplicatesEnabled(False)

    def updateForm(self):
        #self.cbApproximationForm.addItem(self.cbApproximationForm.currentText())
        updflag=0
        if self.approximation:
            v=deepcopy(self.approximation.params)
            mn=deepcopy(self.approximation.parsMin)
            mx=deepcopy(self.approximation.parsMax)
            updflag=1
        self.approximation=abstractModel(self.cbApproximationForm.currentText())
        if self.parent().exps:
            self.approximation.expParams=self.parent().exps[0].data.keys()
            self.approximation.ycol=self.parent().conf['yaxis']
        if updflag:
            for k in v.keys():
                if k in self.approximation.params:
                    self.approximation.params[k]=v[k]
                    self.approximation.parsMin[k]=mn[k]
                    self.approximation.parsMax[k]=mx[k]
        p=QPixmap()
        p.loadFromData(self.approximation.formulaToPng())
        self.lFormula.setPixmap(p)
        self.updateParametersTable()
        self.tableIntervals.clear()
        self.tableIntervals.setColumnCount(2)
        self.tableIntervals.setRowCount(len(self.approximation.vars))
        for i, p in enumerate(self.approximation.vars):
            try:
                p=list(self.approximation.expParams)[int(p[1:])-1]
                s=gl.varSymbols[p]
            except:
                s=p
            b=QPixmap()
            b.loadFromData(renderFormula(s, dpi=100, fontsize=10, convertFormula=False))
            c1=QTableWidgetItem()
            c1.setFlags(c1.flags()^2)
            c1.setIcon(QIcon(b))
            self.tableIntervals.setItem(i,0,c1)

    def updateParametersTable(self):
        self.tParameters.setRowCount(len(self.approximation.params))
        i=0
        for k,v in self.approximation.params.items():
            c1=QTableWidgetItem()
            c1.setFlags(c1.flags()^2)
            c1.setText(k)
            self.tParameters.setItem(i,0,c1)
            c2=QTableWidgetItem()
            c2.setText(str(v))
            self.tParameters.setItem(i,1,c2)
            c3=QTableWidgetItem()
            c3.setFlags(c3.flags()^2)
            c3.setCheckState(2 if k in self.approximation.varParams else 0)
            self.tParameters.setItem(i,2,c3)
            c4=QTableWidgetItem()
            c4.setText(str(self.approximation.parsMin[k]))
            self.tParameters.setItem(i,3,c4)
            c5=QTableWidgetItem()
            c5.setText(str(self.approximation.parsMax[k]))
            self.tParameters.setItem(i,4,c5)
            i+=1

    def calculateParameters(self):
        self.approximation.varParams=[]
        for i in range(self.tParameters.rowCount()):
            k=self.tParameters.item(i,0).text()
            if k in self.approximation.params:
                v=float(self.tParameters.item(i,1).text())
                self.approximation.params[k]=v
                if self.tParameters.item(i,2).checkState()==2:
                    self.approximation.varParams.append(k)
                t=self.tParameters.item(i,3).text()
                self.approximation.parsMin[k]=float(t) if t!='' else ''
                t=self.tParameters.item(i,4).text()
                self.approximation.parsMax[k]=float(t) if t!='' else ''
        try:
            self.approximation.approximateData(self.parent().exps,\
            ycol=self.parent().conf['yaxis'], method=self.cbMethod.currentText())
        except:
            mb=QMessageBox(self)
            mb.setText(u'Не удалось найти решение.\nПопробуйте изменить начальные значения\nили ограничения.')
            mb.setWindowTitle(u'Решение не получено.')
            mb.setIcon(QMessageBox.Critical)
            mb.exec_()
            return
#        self.parent().log.appendPlainText('r^2={:.5f}'.format(self.approximation.r2))
        self.tNotes.setPlainText('')
        self.tNotes.appendPlainText(u'Параметры аппроксимации определены на базе следующих экспериментов:')
        for e in self.parent().exps:
            self.tNotes.appendPlainText(e.name)
        self.tNotes.appendPlainText('r^2={:.5f}'.format(self.approximation.r2))
        for i in range(self.tParameters.rowCount()):
            k=self.tParameters.item(i,0).text()
            if k in self.approximation.params:
                self.tParameters.item(i,1).setText(str(self.approximation.params[k]))

#        print(self.approximation.varParams)
#        print(self.approximation.params)
#        print(self.approximation.parsMin)
#        print(self.approximation.parsMax)


    def redraw(self):
        if self.lines:
            for l in self.lines:
                l.remove()
        if self.rbOnData.isChecked():
            self.lines=self.approximation.plotOnDataPoints(data=self.parent().exps, xcol=self.parent().conf['xaxis'], ax=self.parent().mpl.ax)
        else:
            intervals=[]
            for i in range(self.tableIntervals.rowCount()):
                intervals.append(str2interval(self.tableIntervals.item(i,1).text()))
            xcol=self.parent().conf['xaxis']
            if xcol>self.parent().conf['yaxis']:
                xcol-=1
            self.lines=self.approximation.plotOnIntervalPoints(intervals=intervals, xcol=xcol, ax=self.parent().mpl.ax)            
        self.parent().mplRedraw()

    def accept(self):
        self.approximation.comment=self.tNotes.toPlainText()
        i=QTreeWidgetItem(type=1006)
        i.setToolTip(0, splitStrByNSymbols(self.approximation.comment, gl.ttN))
        i.setText(0,self.approximation.form)
        i.setData(0,100,self.approximation)
        if not self.et in self.parent().models.keys():
            self.parent().models[self.et]=[]
        if not self.approximation.form in self.parent().models[self.et]:
            self.parent().models[self.et].append(self.approximation.form)
        self.item.addChild(i)
        for l in self.lines:
            l.remove()
        self.parent().mplRedraw()
        self.done(1)

    def reject(self):
        for l in self.lines:
            l.remove()
        self.parent().mplRedraw()
        self.done(0)

