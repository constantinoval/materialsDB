# -*- coding: cp1251 -*-
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic

class dialogShowTable(QDialog):
    def __init__(self, parent=None, item=None):
        super(QDialog, self).__init__(parent)
        uic.loadUi('tableView.ui', self)
        self.item=item
        self.updateTable()
        self.tableWidget.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.horizontalHeader().customContextMenuRequested.connect(self.tableColMenu)
        self.tableWidget.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.verticalHeader().customContextMenuRequested.connect(self.tableRowMenu)

    def updateTable(self):
        exp=self.item.data(0,100)
        self.tableWidget.setColumnCount(exp.N)
        self.tableWidget.setHorizontalHeaderLabels(exp.data.keys())
        self.tableWidget.setRowCount(exp.pointsCount)
        for j in range(exp.N):
            for i, v in enumerate(exp[j]):
#                w=QTableWidgetItem(str(v))
                w=QTableWidgetItem()
                w.setData(Qt.EditRole, v)
                self.tableWidget.setItem(i, j, w)
        if hasattr(exp, 'notes'):
            self.ptNotes.document().setPlainText(exp.notes)
        self.leW.setText(str(exp.w))
        self.leExpType.setText(exp.type)

    def accept(self):
        exp=self.item.data(0,100)
        exp.data.clear()
        for jj in range(self.tableWidget.columnCount()):
            nc=[]
            for j in range(self.tableWidget.columnCount()):
                if self.tableWidget.visualColumn(j)==jj:
                    break
            for i in range(self.tableWidget.rowCount()):
                nc.append(float(self.tableWidget.item(i, j).data(Qt.EditRole)))
            exp[self.tableWidget.horizontalHeaderItem(j).text()]=nc
        exp.notes=self.ptNotes.toPlainText()
        exp.w=float(self.leW.text())
        exp.type=self.leExpType.text()

        self.done(1)

    def reject(self):
        self.done(0)
        
    def tableColMenu(self, point):
        m=QMenu(self.tableWidget.horizontalHeader())
        c=self.tableWidget.horizontalHeader().logicalIndexAt(point)
        c=self.tableWidget.horizontalHeader().visualIndex(c)
        m.addAction('Удалить столбец', lambda: self.deleteCol(c))
        m.addAction('Добавить столбец до', lambda: self.addCol(c))
        m.addAction('Добавить столбец после', lambda: self.addCol(c+1))
        m.addAction('Установить имя столбца', lambda: self.setColName(c))
        m.addAction('Установить значение в ячейках столбца', lambda: self.setColValue(c))
        m.addAction('Переместить вправо', lambda: self.moveCol(c, 1))
        m.addAction('Переместить влево', lambda: self.moveCol(c, -1))
        m.addAction('Сортировать', lambda: self.sortByCol(c))
        m.addAction('Преобразовать', lambda: self.calcCol(c))        
        m.exec_(self.tableWidget.horizontalHeader().mapToGlobal(point))

    def sortByCol(self, col):
        self.tableWidget.sortItems(col)

    def deleteCol(self, col):
        self.tableWidget.removeColumn(col)
    
    def addCol(self, col):
        self.tableWidget.insertColumn(col)
        n, ok = QInputDialog.getText(self, 'Имя параметра', 'Имя параметра', text=str(col+1))
        if not ok:
            n=str(col+1)
        i=QTableWidgetItem(n)
        self.tableWidget.setHorizontalHeaderItem(col, i)
        
    def setColName(self, col):
        n, ok = QInputDialog.getText(self, 'Имя параметра', 'Имя параметра',\
                                     text=self.tableWidget.horizontalHeaderItem(col).text())
        if ok:
            self.tableWidget.horizontalHeaderItem(col).setText(n)

    def setColValue(self, col):
        n, ok = QInputDialog.getText(self, 'Имя параметра', 'Имя параметра')
        if ok:
            for j in range(self.tableWidget.rowCount()):
                if self.tableWidget.item(j, col):
                    self.tableWidget.item(j, col).setData(Qt.EditRole, float(n))
                else:
                    i=QTableWidgetItem()
                    i.setData(Qt.EditRole, float(n))
                    self.tableWidget.setItem(j,col,i)

    def calcCol(self, col):
        s, ok = QInputDialog.getText(self, 'Введите выражение', 'Выражение')
        for jj in range(self.tableWidget.columnCount()):
            for j in range(self.tableWidget.columnCount()):
                if self.tableWidget.visualColumn(j)==col:
                    col=j
                    break
        if ok and s:
            for j in range(self.tableWidget.rowCount()):
                x=float(self.tableWidget.item(j, col).data(Qt.EditRole))
                exec('y='+s.replace('x', str(x)))
                self.tableWidget.item(j, col).setData(Qt.EditRole, locals()['y'])

    def moveCol(self, col, direction):
        if col==0 and direction==-1:
            return
        if col==self.tableWidget.columnCount()-1 and direction==1:
            return         
        self.tableWidget.horizontalHeader().moveSection(col, col+direction) 
        
    def tableRowMenu(self, point):
        m=QMenu(self.tableWidget.verticalHeader())
        r=self.tableWidget.verticalHeader().logicalIndexAt(point)
        r=self.tableWidget.verticalHeader().visualIndex(r)
        m.addAction('Удалить строку', lambda: self.deleteRow(r))
        m.addAction('Добавить строку до', lambda: self.addRow(r))
        m.addAction('Добавить строку после', lambda: self.addRow(r+1))
        m.addAction('Переместить вверх', lambda: self.moveRow(r, -1))
        m.addAction('Переместить вниз', lambda: self.moveRow(r, 1))
        m.exec_(self.tableWidget.verticalHeader().mapToGlobal(point))
    
    def deleteRow(self, row):
        if self.tableWidget.selectedItems():
            idx=set(map(lambda x: x.row(), self.tableWidget.selectedIndexes()))
            idx=list(idx)
            idx.sort(reverse=True)
        else:
            idx=[row]
        for r in idx:
            self.tableWidget.removeRow(r)
    
    def addRow(self, row):
        self.tableWidget.insertRow(row)

    def moveRow(self, row, direction):
        if row==0 and direction==-1:
            return
        if row==self.tableWidget.rowCount()-1 and direction==1:
            return         
        self.tableWidget.verticalHeader().moveSection(row, row+direction) 