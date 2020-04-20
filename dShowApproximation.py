from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from lib4db import *
from PyQt5 import uic
from copy import deepcopy
import globalConstants as gl

class dShowApproximation(QDialog):
    def __init__(self, parent=None, item=None):
        super(QDialog, self).__init__(parent)
        uic.loadUi('dShowApproximation.ui', self)
        self.approximation=item.data(0,100).copy()
        #self.parent=parent
        self.lines=[]
        self.initForm()
        self.tParameters.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tParameters.customContextMenuRequested.connect(self.tableMenu)
        self.bRedraw.clicked.connect(self.redraw) 
        
    def initForm(self):
        self.tNotes.setPlainText(self.approximation.comment)
#        self.leForm.setText(self.approximation.form)
        params=self.approximation.params
        self.tParameters.setColumnCount(3)
        self.tParameters.setHorizontalHeaderLabels(['Parameter', 'Value', 'Comment'])
        self.unchangebleParamsCount=len(self.approximation.getParametersFromForm())
        self.tParameters.setRowCount(len(params))
#        if self.approximation.expType in allExpTypes:
#            for i, v in enumerate(varSymbols[self.approximation.expType]):
#                s=('x_{%i}' % (i+1)) + '-'+v
#                p=QPixmap()
#                p.loadFromData(renderFormula(s, dpi=100, fontsize=10, convertFormula=False))
#                l=QLabel()
#                l.setPixmap(p)
#                self.hlVariables.addWidget(l)
        i=0
        for k, v in params.items():
            c1=QTableWidgetItem()
            if i<self.unchangebleParamsCount:
                c1.setFlags(c1.flags()^2)
            c1.setText(k)
            self.tParameters.setItem(i,0,c1)
            c2=QTableWidgetItem()
            c2.setText(str(v))
            self.tParameters.setItem(i,1,c2)
            if self.approximation.comments.get(k,''):
                c3=QTableWidgetItem()
                c3.setText(self.approximation.comments[k])
                self.tParameters.setItem(i,2,c3)
            i+=1
        p=QPixmap()
        p.loadFromData(self.approximation.formulaToPng())
        self.lFormula.setPixmap(p)
        self.tableIntervals.clear()
        self.tableIntervals.setColumnCount(2)
        self.tableIntervals.setRowCount(0)
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
            
    def tableMenu(self, point):
        m=QMenu(self.tParameters)
        m.addAction('add parameter', self.addParameter)
        it=self.tParameters.itemAt(point)
        r=self.tParameters.row(it)
        if r>=self.unchangebleParamsCount:
            m.addAction('delete parameter', lambda: self.deleteParameter(r))            
        m.exec_(self.tParameters.mapToGlobal(point))
        
    def addParameter(self):
        n=self.tParameters.rowCount()
        self.tParameters.setRowCount(n+1)
    
    def deleteParameter(self, row):
        self.tParameters.removeRow(row)

    def updateParametersFromTable(self):
        n=self.tParameters.rowCount()
        self.approximation.comments={}
        self.approximation.params={}
        for i in range(n):
            try:
                k=self.tParameters.item(i,0).text()
            except:
                continue
            try:
                v=float(self.tParameters.item(i,1).text())
            except:
                v=0
            try:
                c=self.tParameters.item(i,2).text()
            except:
                c=''
            self.approximation.params[k]=v
            self.approximation.comments[k]=c
        
    def accept(self):
        self.approximation.comment=self.tNotes.toPlainText()
        self.parent().item.setToolTip(0, splitStrByNSymbols(self.approximation.comment, gl.ttN))
        self.updateParametersFromTable()
        self.parent().item.setData(0,100,self.approximation)
        for l in self.lines:
            l.remove()
        self.parent().mplRedraw()
        self.done(1)
   
    def redraw(self):
        self.updateParametersFromTable()
        self.approximation.evaluateFunction()
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
    
    def reject(self):
        for l in self.lines:
            l.remove()
        self.parent().mplRedraw()
        self.done(0)
