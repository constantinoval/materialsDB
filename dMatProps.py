# -*- coding: cp1251 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import globalConstants as gl
from importlib import reload

class dMatProps(QDialog):
    def __init__(self, parent=None, item=None):
        reload(gl)
        super(QDialog, self).__init__(parent)
        uic.loadUi('dMatProps.ui', self)
        self.item=item
        self.completer=QCompleter(gl.matCompletions)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.initForm()
        self.tProperties.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tProperties.customContextMenuRequested.connect(self.tableMenu)
        
    def initForm(self):
        params=self.item.data(0,100)
        if not params:
            params={}
        self.ptComment.setPlainText(self.item.data(0,101))
        self.tProperties.setColumnCount(3)
        self.tProperties.setHorizontalHeaderLabels(['Parameter', 'Value', 'Comment'])
        self.tProperties.setRowCount(len(params))
        for i, p in enumerate(params):
            le=QLineEdit()
            le.setText(p[0])
            le.setCompleter(self.completer)
            le.setFrame(False)
            self.tProperties.setCellWidget(i,0,le)
            c2=QTableWidgetItem()
            c2.setText(p[1])
            self.tProperties.setItem(i,1,c2)
            c3=QTableWidgetItem()
            c3.setText(p[2])
            self.tProperties.setItem(i,2,c3)
            
    def tableMenu(self, point):
        m=QMenu(self.tProperties)
        m.addAction('add parameter', self.addParameter)
        it=self.tProperties.itemAt(point)
        r=self.tProperties.row(it)
        m.addAction('delete parameter', lambda: self.deleteParameter(r))            
        m.exec_(self.tProperties.mapToGlobal(point))
        
    def addParameter(self):
        n=self.tProperties.rowCount()
        self.tProperties.setRowCount(n+1)
        le=QLineEdit()
        le.setCompleter(self.completer)
        le.setFrame(False)
        self.tProperties.setCellWidget(n,0,le)
    
    def deleteParameter(self, row):
        self.tProperties.removeRow(row)

    def updateParametersFromTable(self):
        params=[]
        n=self.tProperties.rowCount()
        for i in range(n):
            try:
                k=self.tProperties.cellWidget(i,0).text()
            except:
                continue
            try:
                v=self.tProperties.item(i,1).text()
            except:
                v=''
            try:
                c=self.tProperties.item(i,2).text()
            except:
                c=''
            params.append([k,v,c])
        self.item.setData(0,101,self.ptComment.toPlainText())
        self.item.setData(0,100,params)
