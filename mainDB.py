# -*- coding: cp1251 -*-
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvas as Canvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavTB
from matplotlib.figure import Figure
from lib4db import *
import pickle
from dialogAddExperiment import *
from dialogApproximation import *
from dShowApproximation import *
from dCalcAdiabatic import *
from dTextInput import *
from dMatProps import *
from dMplSetup import *
from dialogTableView import dialogShowTable
from copy import deepcopy
import icons
import json
import os
from shutil import copyfile
import globalConstants as gl
import itertools
import xlwt


class MatplotlibWidget(Canvas):
    def __init__(self, parent=None):
        figure = Figure(figsize=(4, 3))
        self.ax = figure.add_subplot(111)
        Canvas.__init__(self, figure)
        c = Canvas(Figure())
        self.setParent(parent)
        Canvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        Canvas.updateGeometry(self)
        self.figure = figure
        self.ax.grid()
        self.tb = NavTB(self.figure.canvas, parent)
        self.tb.hide()
        self.marker = itertools.cycle(('s', 'v', 'd', 'o', '*', '^', '8'))


#        self.ax.set_xlabel(u'пластическая деформация/скорость деформации')
#        self.ax.set_ylabel(u'напряжение/деформация разрушения')
#        self.figure.set_tight_layout(True)

expTypes = {0: 'c', 1: 't', 2: 's', 3: 'ef'}
expTypes2 = {'c': 0, 't': 1, 's': 2, 'ef': 3}
plotStyles = {'c': '-', 't': '-', 'ef': 'o'}
compatibleExperiments = [['t', 'c', 's'], ['ef']]


class MyWindow(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        uic.loadUi('mainDB2.ui', self)
        #        l = QVBoxLayout(self.widget)
        self.mpl = MatplotlibWidget(self.widget)
        self.mplLayout.addWidget(self.mpl)
        #        self.toolBar.addAction(self.dockWidget_2.toggleViewAction())
        self.toolBar.addAction(self.dockWidget.toggleViewAction())
        self.lines = {}
        self.xcol = 0
        self.ycol = 1
        self.exps = []
        self.icons = {}
        self.icons['trash'] = QIcon(":/icons/trash")
        self.icons['x'] = QIcon(":/icons/x")
        self.icons['notes'] = QIcon(":/icons/notes")
        self.icons['c'] = QIcon(":/icons/compression")
        self.icons['t'] = QIcon(":/icons/compression")
        self.icons['s'] = QIcon(":/icons/compression")
        self.icons['ef'] = QIcon(":/icons/compression")
        self.icons['add'] = QIcon(":/icons/add")

        if os.path.exists('matDB.cfg'):
            self.conf = json.load(open('matDB.cfg', 'r'))
        else:
            self.conf = {}
            self.conf['showMaterialNameInLegend'] = False
            self.conf['showErrorBars'] = True
            self.conf['showGrid'] = True
            self.conf['showLegend'] = True
            self.conf['fixedAxisLabels'] = False
            self.conf['xlabel'] = ''
            self.conf['ylabel'] = ''
            self.conf['workDir'] = ''
            self.conf['lw'] = 1.0
            self.conf['ms'] = 1.0
            self.conf['ls'] = '-'
            self.conf['dbFile'] = 'materials.pcl'
        self.conf['autox'] = True
        self.conf['autoy'] = True
        self.conf['xbound'] = (0, 1)
        self.conf['ybound'] = (0, 1)
        self.conf['xaxis'] = 0
        self.conf['yaxis'] = 1
        try:
            self.models = json.load(open('models.json', 'r'))
        except:
            self.models = {}
        self.readDB()
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setExpandsOnDoubleClick(False)
        self.treeWidget.setUniformRowHeights(True)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.showContext)
        self.mpl.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mpl.customContextMenuRequested.connect(self.showMplContext)
        self.treeWidget.doubleClicked.connect(self.tWidgetDblClicked)
        self.treeWidget.itemChanged.connect(self.plotDiagram)
        self.actionAddMaterial.setIcon(self.icons['add'])
        self.plottedItems = []
        self.colors = []

    def readDB(self):
        try:
            with open(self.conf.get('dbFile', 'materials.pcl'), 'rb') as f:
                materials = pickle.load(f)
            self.log.appendPlainText(u'Данные считаны: ' + self.conf['dbFile'])
        except:
            materials = []
        for m in materials:
            self.addMaterial(m)

    def plotDiagram(self, item):
        if item.type() != 1005:
            return
        self.treeWidget.blockSignals(True)
        if item.checkState(0) == 2:
            matname = item.parent().parent().text(0)
            self.treeWidget.blockSignals(True)
            exp = item.data(0, 100)
            if self.exps:
                add = self.exps[-1].type == exp.type
                if not add:
                    for ce in compatibleExperiments:
                        add = add or self.exps[-1].type in ce and exp.type in ce
                #                add=add and self.exps[-1].N==exp.N
                if not add:
                    for l in self.plottedItems:
                        l.setCheckState(0, 0)
                        del self.lines[l.data(0, 101)[0]]
                        for ll in l.data(0, 101):
                            ll.remove()
                        l.setData(0, 101, None)
                    self.exps = []
                    self.plottedItems = []
            lineStyle = '-' if '-' in self.conf['ls'] else ''
            lineStyle += next(self.mpl.marker) if 'o' in self.conf['ls'] else ''
            if exp.has_key(exp.key(self.conf['yaxis']) + 'err') and self.conf['showErrorBars']:
                l = self.mpl.ax.errorbar(exp[self.conf['xaxis']], exp[self.conf['yaxis']],
                                         yerr=exp[exp.key(self.conf['yaxis']) + 'err'],
                                         lw=self.conf['lw'])  # , label=matname+': '+item.text(0))
                self.lines[l[0]] = ['', matname + ': '][self.conf['showMaterialNameInLegend']] + item.text(0)
                l = [l[0], l[2][0]]
            else:
                l = self.mpl.ax.plot(exp[self.conf['xaxis']], exp[self.conf['yaxis']], lineStyle,
                                     lw=self.conf['lw'], ms=self.conf['ms'])  # , label=matname+': '+item.text(0))
                self.lines[l[0]] = ['', matname + ': '][self.conf['showMaterialNameInLegend']] + item.text(0)
                l = [l[0]]
            self.exps.append(exp)
            item.setData(0, 101, l)
            self.plottedItems.append(item)
            #            if len(self.colors)<len(self.exps):
            #                self.colors.append(l[0].get_color())
            #            else:
            #                c=self.colors[len(self.exps)-1]
            #                for ll in l:
            #                    ll.set_color(c)
            self.treeWidget.blockSignals(False)
        if item.checkState(0) == 0:
            if not item.data(0, 100) in self.exps:
                self.treeWidget.blockSignals(False)
                return
            self.exps.remove(item.data(0, 100))
            del self.lines[item.data(0, 101)[0]]
            for ll in item.data(0, 101):
                ll.remove()
            item.setData(0, 101, None)
            self.plottedItems.remove(item)
        self.treeWidget.blockSignals(False)
        self.mplRedraw()

    def mplSetup(self):
        dialog = dMplSetup(self)
        dialog.setModal(True)
        dialog.exec()
        if not dialog.result():
            return
        self.conf['showMaterialNameInLegend'] = dialog.cbMatName.isChecked()
        self.conf['showErrorBars'] = dialog.cbShowErrorBars.isChecked()
        self.conf['showLegend'] = dialog.cbShowLegend.isChecked()
        self.conf['showGrid'] = dialog.cbShowGrid.isChecked()
        self.conf['xscale'] = ['linear', 'log'][dialog.cbLogScale.isChecked()]
        self.mpl.ax.grid(self.conf['showGrid'])
        self.conf['fixedAxisLabels'] = dialog.cbFixedAxisLabels.isChecked()
        self.conf['ls'] = ''
        if dialog.cbLine.isChecked():
            self.conf['ls'] += '-'
        if dialog.cbMarker.isChecked():
            self.conf['ls'] += 'o'
        self.conf['lw'] = dialog.leLineWidth.value()
        self.conf['ms'] = dialog.leMarkerSize.value()
        self.conf['xaxis'] = dialog.cbXaxis.currentIndex()
        self.conf['yaxis'] = dialog.cbYaxis.currentIndex()
        self.mpl.ax.set_xscale(self.conf['xscale'])
        self.conf['autox'] = dialog.cbXautoscale.isChecked()
        self.conf['autoy'] = dialog.cbYautoscale.isChecked()
        self.conf['xbound'] = (float(dialog.leXmin.text()), float(dialog.leXmax.text()))
        self.conf['ybound'] = (float(dialog.leYmin.text()), float(dialog.leYmax.text()))
        if self.conf['fixedAxisLabels']:
            self.conf['xlabel'] = dialog.leXLabel.text()
            self.conf['ylabel'] = dialog.leYLabel.text()
        pli = list(self.plottedItems)
        for item in pli:
            item.setCheckState(0, 0)
        for item in pli:
            item.setCheckState(0, 2)

    def addMaterial(self, material):
        newmat = QTreeWidgetItem(type=1000)
        newmat.setText(0, material['name'])
        #        newmat.setEditable(False)
        #        newmat.setData(0,100,material)
        self.treeWidget.addTopLevelItem(newmat)
        for i, fields in enumerate(
                [u'Свойства материала', u'Примечания', u'Экспериментальные данные', u'Аппроксимации']):
            e = QTreeWidgetItem(type=1001 + i)
            e.setText(0, fields)
            #            if i==1:
            #                e.setIcon(0,self.icons['notes'])
            #            e.setEditable(False)
            newmat.addChild(e)
        newmat.child(0).setData(0, 100, material.get('matProps', {}))
        newmat.child(0).setData(0, 101, material.get('matPropsComment', ''))
        newmat.child(1).setData(0, 100, material.get('comment', ''))
        newmat.setToolTip(0, splitStrByNSymbols(material.get('comment', ''), gl.ttN))
        newmat.child(1).setToolTip(0, splitStrByNSymbols(material.get('comment', ''), gl.ttN))
        ditem = newmat.child(2)
        for exp in material['diagrams']:
            name = exp.name
            ee = QTreeWidgetItem(type=1005)
            ee.setText(0, name)
            #            ee.setIcon(0, self.icons[exp.type])
            #            ee.setCheckable(True)
            ee.setCheckState(0, 0)
            ee.setData(0, 100, exp)
            ditem.addChild(ee)
        for a in material['approximations']:
            ee = QTreeWidgetItem(type=1006)
            ap = abstractModel(a['func'])
            ee.setText(0, ap.form)
            ap.resumeFromDic(a)
            ee.setData(0, 100, ap)
            ee.setToolTip(0, splitStrByNSymbols(a['comment'], gl.ttN))
            newmat.child(3).addChild(ee)

    def showContext(self, point):
        index = self.treeWidget.currentIndex()
        item = self.treeWidget.itemFromIndex(index)
        if not item:
            return
        m1 = QMenu(self.treeWidget)
        if item.type() == 1003:
            m1.addAction(u'Расчет адиабатического разогрева', lambda: self.calcAdiabatic(item))
            m1.addAction(u'Сбросить все весовые коэффициенты', lambda: self.resetW(item))
            a = m1.addAction(u'Добавить эксперимент', lambda: self.addDiagram(item))
            a.setIcon(self.icons['add'])
            m1.addAction(u'Добавить пустой эксперимент', lambda: self.addEmpty(item))
            m1.addAction('Выделить все', lambda: self.selAll(item))
            m1.addAction('Снять все выделения', lambda: self.selAll(item, 0))
            m1.addAction('Экспортировать в Excel', lambda: self.exportToXLS(item))
            m1.addAction('Сохранить функцию свойств в BDM', lambda: self.exportMatFunctionToBDM(item))
            m1.addAction('select compression')
            m1.addAction('select tension')
            m1.addAction('select shear')
        if item.type() == 1004:
            a = m1.addAction('add approximation', lambda: self.addApproximation(item))
            a.setIcon(self.icons['add'])
        if item.type() == 1005:
            #            a=m1.addAction('Показать таблицу', lambda: self.showTable(item))
            a = m1.addAction('Переименовать', lambda: self.rename(item))
            a = m1.addAction('Удалить', lambda: self.removeDiagOrApproximation(item, 'diagrams'))
            a.setIcon(self.icons['x'])
            a = m1.addAction('Обновить имя', lambda: self.updateExpName(item))
        if item.type() == 1006:
            a = m1.addAction('remove', lambda: self.removeDiagOrApproximation(item, 'approximations'))
            a.setIcon(self.icons['x'])
        if item.type() == 1000:
            a = m1.addAction(u'Удалить', lambda: self.removeMaterial(item))
            a.setIcon(self.icons['x'])
            a = m1.addAction(u'Копировать', lambda: self.cloneMaterial(item))
            a = m1.addAction(u'Переименовать', lambda: self.rename(item))
        m1.exec(self.treeWidget.mapToGlobal(point))

    def updateExpName(self, item):
        updateFlag = (item in self.plottedItems) and (item.checkState(0) == 2)
        exp = item.data(0, 100)
        name = exp.name
        exp.autoName = True
        exp.updateName()
        self.treeWidget.blockSignals(True)
        item.setText(0, exp.name)
        self.treeWidget.blockSignals(False)
        if updateFlag and name != exp.name:
            item.setCheckState(0, 0)
            item.setCheckState(0, 2)

    def rename(self, item):
        n, ok = QInputDialog.getText(self, 'Input new material name', 'New material name', text=item.text(0))
        if ok:
            self.treeWidget.blockSignals(True)
            item.setText(0, n)
            if hasattr(item.data(0, 100), 'name'):
                item.data(0, 100).name = n
            self.treeWidget.blockSignals(False)

    def tWidgetDblClicked(self, index):
        item = self.treeWidget.itemFromIndex(index)

        if item.type() == 1003:
            self.addDiagram(item)

        if item.type() == 1004:
            self.addApproximation(item)

        if item.type() == 1006:
            self.showApproximation(item)

        if item.type() == 1001:
            self.editMatProps(item)

        if item.type() == 1005:
            self.showTable(item)

        if item.type() == 1000:
            self.renameMaterial(item)

        if item.type() == 1002:
            self.editComment(item)

    def expName(self, exp):
        de = exp.meanDE()
        fs = '{1:6.3e}' if de < 1 else '{1:6.0f}'
        name = '{0}, '
        if exp.expType != 'ep':
            name += 'de=' + fs + ', '
        else:
            name += 'ss={1:.4f}, '
        name += 'T={2}'
        return name.format(exp.expType, de, exp.T0)

    def addDiagram(self, item):
        fnames = QFileDialog.getOpenFileNames(directory=self.conf.get('workDir', ''), filter='*.txt;*.pl')[0]
        if not fnames:
            return
        self.conf['workDir'] = os.path.split(fnames[0])[0]
        for fname in fnames:
            exp = experimentalData(fname)
            exp.updateName()
            ee = QTreeWidgetItem(type=1005)
            ee.setText(0, exp.name)
            ee.setCheckState(0, 0)
            ee.setData(0, 100, exp)
            item.addChild(ee)

    def closeEvent(self, event):
        self.saveData()
        json.dump(self.conf, open('matDB.cfg', 'w'))
        json.dump(self.models, open('models.json', 'w'), indent=5)
        json.dump({'conf': self.conf, 'models': self.models}, open('test.cfg', 'w'), indent=5)

    @pyqtSlot()
    def on_actionAddMaterial_triggered(self):
        n, ok = QInputDialog.getText(self, 'Input new material name', 'New material name')
        if ok:
            newMat = deepcopy(materialDic)
            newMat['name'] = n
            self.addMaterial(newMat)

    #            self.materials.append(newMat)

    @pyqtSlot()
    def on_actionSaveDB_triggered(self):
        self.saveData()
        self.log.appendPlainText(u'Данные сохранены: ' + self.conf['dbFile'])

    def addApproximation(self, item):
        if not self.exps:
            mb = QMessageBox(self)
            mb.setText('Для аппроксимации должна быть активна хотя бы одна диаграмма')
            mb.setWindowTitle('Ошибка')
            mb.setIcon(QMessageBox.Critical)
            mb.exec_()
            return
        dialog = dDataApproximation(self, item)
        dialog.setModal(False)
        dialog.show()

    def selAll(self, parent, state=2):
        n = parent.childCount()
        for i in range(n):
            parent.child(i).setCheckState(0, state)

    def mplRedraw(self):
        self.mpl.ax.set_autoscalex_on(self.conf['autox'])
        self.mpl.ax.set_autoscaley_on(self.conf['autoy'])
        self.mpl.ax.relim(True)
        self.mpl.ax.autoscale_view()
        if self.conf['autox']:
            self.conf['xbound'] = self.mpl.ax.get_xlim()
        else:
            self.mpl.ax.set_xlim(self.conf['xbound'])
        if self.conf['autoy']:
            self.conf['ybound'] = self.mpl.ax.get_ylim()
        else:
            self.mpl.ax.set_ylim(self.conf['ybound'])
        if not self.conf['fixedAxisLabels'] and self.exps:
            exp = self.exps[-1]
            self.conf['xlabel'] = gl.names[exp.key(self.conf['xaxis'])]
            self.conf['ylabel'] = gl.names[exp.key(self.conf['yaxis'])]
        self.mpl.ax.set_xlabel(self.conf['xlabel'])
        self.mpl.ax.set_ylabel(self.conf['ylabel'])
        self.mpl.figure.canvas.draw_idle()
        if self.conf['showLegend']:
            self.legend = self.mpl.ax.legend(tuple(self.lines.keys()), tuple(self.lines.values()))
            self.legend.draggable(True)
        else:
            try:
                self.legend.remove()
            except:
                pass

    def removeDiagOrApproximation(self, item, it):
        matIndex = self.treeWidget.indexFromItem(item.parent().parent()).row()
        chIndex = self.treeWidget.indexFromItem(item).row()
        if it == 'diagrams':
            item.setCheckState(0, 0)
        item.parent().takeChild(chIndex)

    #        self.materials[matIndex][it].pop(chIndex)

    def removeMaterial(self, item):
        #        matIndex=self.treeWidget.indexFromItem(item).row()
        matIndex = self.treeWidget.indexOfTopLevelItem(item)
        self.selAll(item.child(2), 0)
        self.treeWidget.takeTopLevelItem(matIndex)

    #        self.materials.pop(matIndex)

    @pyqtSlot()
    def on_tbApplyFilter_clicked(self):
        txtToFind = self.leFilter.text()
        self.treeWidget.setHidden(True)
        for i in range(self.treeWidget.topLevelItemCount()):
            tl = self.treeWidget.topLevelItem(i)
            txt = tl.text(0)
            tl.setHidden(not txtToFind.upper() in txt.upper())
        self.treeWidget.setHidden(False)

    def saveData(self):
        fname = self.conf.get('dbFile', 'materials.pcl')
        dr = os.path.split(os.path.abspath(self.conf.get('dbFile', 'materials.pcl')))[0]
        materials = []
        if os.path.exists(fname):
            copyfile(fname, fname[:-3] + 'bkp')
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            m = self.convertItemToSave(item)
            materials.append(m)
            with open(fname, 'wb') as f:
                try:
                    pickle.dump(materials, f)
                except:
                    if os.path.exists(fname[:-3] + 'bkp'):
                        copyfile(fname[:-3] + 'bkp', fname)

    def convertItemToSave(self, item):
        m = {}
        m['name'] = item.text(0)
        sitem = item.child(0)
        m['matProps'] = sitem.data(0, 100)
        m['matPropsComment'] = sitem.data(0, 101)
        sitem = item.child(1)
        m['comment'] = sitem.data(0, 100)
        sitem = item.child(2)
        m['diagrams'] = []
        for j in range(sitem.childCount()):
            c = sitem.child(j)
            m['diagrams'].append(c.data(0, 100))
        sitem = item.child(3)
        m['approximations'] = []
        for j in range(sitem.childCount()):
            c = sitem.child(j)
            m['approximations'].append(c.data(0, 100).dicToSave())
        return m

    def showApproximation(self, item):
        dialog = dShowApproximation(self, item)
        dialog.setModal(False)
        self.item = item
        # dialog.exec()
        dialog.show()

    def editMatProps(self, item):
        dialog = dMatProps(self, item)
        dialog.setModal(True)
        rez = dialog.exec()
        if rez:
            dialog.updateParametersFromTable()

    def editComment(self, item):
        dialog = dTextInput(self, item)
        dialog.setModal(True)
        rez = dialog.exec()
        if rez:
            text = dialog.ptComment.toPlainText()
            item.setData(0, 100, text)
            item.setToolTip(0, splitStrByNSymbols(text, gl.ttN))
            item.parent().setToolTip(0, splitStrByNSymbols(text, gl.ttN))

    def changeExpProps(self, item):
        st = item.checkState(0)
        item.setCheckState(0, 0)
        exp = item.data(0, 100)
        dialog = dAddExperiment(self)
        if exp.type in ['t', 'c']:
            dialog.leMeanDE.setText('{}'.format(mean(exp['de'])))
        if exp.type in ['ef']:
            dialog.leMeanDE.setText('{}'.format(mean(exp['ss'])))
        if exp.has_key('T'):
            T0 = mean(exp['T'])
        else:
            T0 = 293
        dialog.leT0.setText(str(T0))
        dialog.leW.setText('{}'.format(exp.w))
        dialog.cbCalcReal.setEnabled(exp.canToReal)
        dialog.cbExpType.setCurrentIndex(expTypes2[exp.type])
        dialog.cbTemp.setChecked(not exp.has_key('T'))
        dialog.setModal(True)
        dialog.exec()
        if not dialog.result():
            return
        if dialog.cbEditDE.isChecked():
            if exp.type != 'ef':
                exp['de'] = float(dialog.leMeanDE.text())
            else:
                exp['ss'] = float(dialog.leMeanDE.text())
        if dialog.cbTemp.isChecked():
            exp['T'] = float(dialog.leT0.text())
        exp.type = expTypes[dialog.cbExpType.currentIndex()]
        exp.w = float(dialog.leW.text())
        if dialog.cbCalcReal.isChecked():
            toReal(exp)
        exp.updateName()
        item.setText(0, exp.name)
        item.setCheckState(0, st)

    def calcAdiabatic(self, item):
        dialog = dCalcAdiabatic(self, item)
        dialog.setModal(True)
        dialog.exec()

    def resetW(self, item):
        n = item.childCount()
        for i in range(n):
            item.child(i).data(0, 100).w = 1
        self.log.appendPlainText(u'Всем весовым коэффициентам присвоено значение 1.')

    def cloneMaterial(self, item):
        nm = self.convertItemToSave(item)
        nm['name'] = nm['name'] + '-copy'
        self.addMaterial(nm)

    def showMplContext(self, point):
        m1 = QMenu(self.mpl)
        m1.addAction('настройка вида', self.mplSetup)
        m1.addAction('сохранить картинку', self.mplSavePicture)
        m1.exec(self.mpl.mapToGlobal(point))

    def mplSavePicture(self):
        f, ok = QFileDialog.getSaveFileName(filter='*.png')
        if not ok:
            return
        self.mpl.figure.savefig(f, bbox_inches='tight')

    #    def resizeEvent(self, event):
    #        print(event.size())
    #        es=event.size()
    #        es.scale(0.666, 1, 0)
    #        self.dockWidget_2.resize(es)

    def showTable(self, item):
        updateFlag = (item in self.plottedItems) and (item.checkState(0) == 2)
        dialog = dialogShowTable(self, item)
        dialog.setModal(True)
        rez = dialog.exec()
        if rez and updateFlag:
            item.setCheckState(0, 0)
            item.setCheckState(0, 2)

    @pyqtSlot()
    def on_actionNewDB_triggered(self):
        for i in self.plottedItems:
            i.setCheckState(0)
        self.exps = []
        self.plottedItems = []
        self.treeWidget.clear()
        self.conf['dbFile'] = os.path.abspath('default.pcl')

    @pyqtSlot()
    def on_actionSaveDBas_triggered(self):
        dr = os.path.abspath(self.conf.get('dbFile', 'materials.pcl'))
        f = QFileDialog.getSaveFileName(self, caption='Сохранить как',
                                        directory=dr, filter='*.pcl;;*.bkp')[0]
        if not f:
            return
        self.conf['dbFile'] = f
        self.saveData()

    @pyqtSlot()
    def on_actionOpenDB_triggered(self):
        dr = os.path.split(os.path.abspath(self.conf.get('dbFile', 'materials.pcl')))[0]
        fname = QFileDialog.getOpenFileName(directory=dr, filter='*.pcl;;*.bkp')[0]
        if not fname:
            return
        self.on_actionNewDB_triggered()
        self.conf['dbFile'] = fname
        self.readDB()

    def exportToXLS(self, parent):
        f, ok = QFileDialog.getSaveFileName(filter='*.xls')
        if not ok:
            return
        n = parent.childCount()
        w = xlwt.Workbook()
        for i in range(n):
            if parent.child(i).checkState(0) == 2:
                d = parent.child(i).data(0, 100)
                sht = w.add_sheet(d.name)
                for j, k in enumerate(d.data.keys()):
                    sht.write(0, j, k)
                    for l in range(len(d.data[k])):
                        sht.write(1 + l, j, d.data[k][l])
        if n:
            w.save(f)

    def exportMatFunctionToBDM(self, parent):
        f, ok = QFileDialog.getSaveFileName(filter='*.txt')
        if not ok:
            return
        n = parent.childCount()
        with open(f, 'w') as fout:
            for i in range(n):
                if parent.child(i).checkState(0) == 2:
                    d = parent.child(i).data(0, 100)
                    dt = 2*(d.data['ep'][1]-d.data['ep'][0])/(d.data['de'][1]+d.data['de'][0])*1000
                    for j in range(len(d.data['ep'])):
                        fout.write("{}\t{}\t{}\t{}\t{}\n".format(d.data['s'][j],  dt*j, d.data['ep'][j], d.data['de'][j], d.data['T'][j]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
