from collections import OrderedDict
from pyparsing import Word, Suppress, alphanums, nums
import lmfit
import numpy as np
import matplotlib.pylab as plt
from math import *
from copy import deepcopy
from sympy import sympify, latex
import matplotlib.pyplot as plt
from io import BytesIO
import os
#from globalConstants import names, varSymbols
from importlib import reload
import globalConstants as gl

def splitStrByNSymbols(s, N=40):
    i=0
    rez=''
    for c in s:
        if i==N:
            i=0
            rez+='\n'
        rez+=c
        i+=1
    return rez

def renderFormula(formula, file=None, fontsize=12, format='png', dpi=300,
                  varSymbols=None, convertFormula=True):
    s=formula.split('=')
    if convertFormula:
        for i in range(len(s)):
            s[i]=latex(sympify(s[i]))
    s='='.join(s)
    if varSymbols:
        for k,v in varSymbols.items():
            s=s.replace(k,v)
    f=plt.figure(figsize=(0.01, 0.01))
    f.text(0,0,r'$'+s+'$', fontsize=fontsize)
    out=BytesIO() if not file else file
    f.savefig(out, format=format, dpi=dpi, transparent=True, bbox_inches='tight',
              pad_inches=0.0, frameon=False)
    if isinstance(out, BytesIO):
        return out.getvalue()
    else:
        return 1
    
def createMesh(intervals, xcol=0):
    if xcol:
        tmp=intervals[0]
        intervals[0]=intervals[xcol]
        intervals[xcol]=tmp
    def nm(l):
        rez=1
        for ll in l:
            rez*=len(ll)
        return rez
    n=[]
    for i in range(1, len(intervals)):
        n.append(nm(intervals[i:]))

    for i in range(2, len(intervals)):
        m=len(intervals[i-1])
        tmp=[[x]*m for x in intervals[i]]
        intervals[i]=[]
        for t in tmp:
            intervals[i]+=t
    for i in range(1, len(intervals)-1):
        intervals[i]*=n[i]
    if xcol:
        tmp=intervals[0]
        intervals[0]=intervals[xcol]
        intervals[xcol]=tmp
    return intervals

def str2interval2(inpStr):
    ll=inpStr.split(':')
    if len(ll)<3:
        return []
    ff=list(map(float, ll))
    if ff[1]<ff[0] or ff[2]==0:
        return [ff[0]]
    rez=[ff[0]]
    dx=(ff[1]-ff[0])/ff[2]
    while len(rez)<ff[2]+1:
        rez.append(rez[-1]+dx)
    return rez

def str2interval(inpStr):
    rez=[]
    for ll in inpStr.split(';'):
        if ':' in ll:
            rez+=str2interval2(ll)
        else:
            rez+=[float(ll)]
    return rez

def numberFormat(num, dec=2):
    if num==0:
        m=1
    else:
        m=log10(num)
    if m>=4 or m<-2:
        fmt='{:.'+str(dec)+'e}'
    else:
        fmt='{:.'+str(dec)+'f}'
    rez=fmt.format(num)
    tmp=rez.split('.')
    rez=[tmp[0]]+tmp[1].split('e')
    rez[1]=rez[1].rstrip('0')
    r=rez[0]
    if rez[1]:
        r+='.'+rez[1]
    if len(rez)==3:
        r+='e'+rez[2]
    return r


allExpTypes=['c', 't', 'ef']

def mean(v):
    if not v:
        return 0
    if len(v)==0:
        return 0
    return sum(v)/len(v)
    
from collections import OrderedDict

class experimentalData:
    def __init__(self, fname=None):
        self.data=OrderedDict()
        self.canToReal=False
        self.w=1.0
        self.notes=''
        self.name=''
        self.autoName=True
        if  fname:
            self.readFromTxt(fname)
            
    def readFromTxt(self, fname):
        with open(fname, 'r') as f:
            l=f.readline().strip()
            if len(l.split())==1:
                self.type=l
                l=f.readline().strip()
            else:
                self.type=''
                self.name=os.path.split(fname)[-1]
                self.autoName=False
            keys=l.split()
            self.data=OrderedDict()
            for k in keys:
                self.data[k]=[]
            self.N=len(keys)
            for l in f:
                ll=l.split()
                for i in range(len(ll)):
                    self.data[keys[i]].append(float(ll[i]))
            self.pointsCount=len(self[0])
            self.canToReal=self.type in ['c', 't']
    
    def key(self, idx):
        return list(self.data.keys())[idx]
                    
    def __getitem__(self, idx):
        if isinstance(idx, int):
            if idx<self.N:
                return list(self.data.values())[idx]
        if isinstance(idx, str):
            return self.data.get(idx, None)
        return None

    def __setitem__(self, idx, val):
        if isinstance(val, int) or isinstance(val, float):
            val=[val]*self.pointsCount
        if isinstance(idx, int):
            if idx<self.N:
                self.data[self.key(idx)]=val
        if isinstance(idx, str):
            self.data[idx]=val
        self.N=len(self.data)
        self.pointsCount=len(val)
       
    def updateName(self):
        if not self.autoName:
            return
        if self.type in ['c', 't', 's']:
            includes=['de', 'T']
        elif self.type in ['ef']:
            includes=['ss', 'T']
        else:
            includes=[]
            self.autoName=False
        nn=self.type+', ' if self.type else ''
        i=0
        for k, v in self.data.items():
            if k in includes:
                m=mean(v)
                nn+=k+'='+numberFormat(m)+', '
            i+=1
        self.name=nn[:-2]
        
    def has_key(self, key):
        return key in self.data
    
    def getCols(self, cols=[]):
        if not cols:
            cols=list(range(self.N))
        if not isinstance(cols, list):
            cols=[cols]
        rez=[]
        for c in cols:
            rez.append(self[c])
        return rez
    
def calcT(expData, k=None, T0=293):
    if not expData.has_key('T'):
        expData['T']=T0
    if not expData.type in ['c','t']:
        return
    if not k or mean(expData['de'])<=1:
        expData['T']=expData['T'][0]
    else:
        N=len(expData['T'])
        expData['T']=[expData['T'][0]]
        for i in range(1, N):
            TT=expData['T'][-1]+k*0.5*(expData['s'][i]+expData['s'][i-1])\
               *(expData['ep'][i]-expData['ep'][i-1])
            expData['T'].append(TT)
        expData.pointsCount=N
    
def toReal(expData):
    if not expData.canToReal:
        return
    sign=[-1,1][expData.type=='t']
    for i in range(expData.pointsCount):
        expData['de'][i]/=(1+sign*expData['ep'][i])
        expData['s'][i]*=(1+sign*expData['ep'][i])
        expData['ep'][i]=sign*log(1+sign*expData['ep'][i])
    expData.canToReal=False      


class abstractModel:
    comments={}
    comment=''
    def __init__(self, form=''):
        self.form=form
        self.name=form
        self.lines=[]
        self.ycol=1
        self.updateForm()
        self.evaluateFunction()

    def updateForm(self):
        self.params=self.getParametersFromForm()
        self.vars=self.getVarsFromForm()
        self.varParams=self.params.keys()
        self.parsMin={}.fromkeys(self.varParams, '')
        self.parsMax={}.fromkeys(self.varParams, '')

    def getParametersFromForm(self):
        p=Suppress('{')+Word(alphanums)+Suppress('}')
        rez=p.searchString(self.form)
        params=OrderedDict().fromkeys([pp[0] for pp in rez.asList()], 0)
        return params

    def getVarsFromForm(self):
        v='x'+Word(nums)
        rez=v.searchString(self.form)
        vars=list(set([''.join(pp) for pp in rez.asList()]))
        vars.sort()
        if not vars:
            vars=['x1']
        return vars
        
    def evaluateFunction(self):
#        print(', '.join(vrs))
#        s='function=lambda x1, x2, x3:'+self.form.format(**self.params)
        s='function=lambda '+', '.join(self.vars)+':'+self.form.format(**self.params)
        exec(s)
        self.function=locals()['function']
        
    def approximateData(self, data, ycol=1, method='leastsq'):
        def residuals(params, X, Y, w):
            p=params.valuesdict()
            rez=[]
            self.params.update(p)
            self.evaluateFunction()
            for xx, yy, ww in zip(X,Y,w):
                rez.append((self.function(*xx)-yy)*ww)
            return np.array(rez)
        if not isinstance(data, list):
            data=[data]
        dataX=[]
        dataY=[]
        w=[]
        xcols=[]
        for v in self.vars:
            xcols.append(int(v[1:])-1)
        for d in data:
            dataX+=zip(*d.getCols(xcols))
            dataY+=(d[ycol])
            w+=[d.w]*len(d[0])
        if len(dataX)<len(self.vars):
            print('Недостаточно колонок независимых переменных.')
            return
        pars=lmfit.Parameters()
        for k, v in self.params.items():
            if k in self.varParams:
                pars.add(k,v)
                if self.parsMin[k]!='':
                    pars[k].set(min=self.parsMin[k])
                if self.parsMax[k]!='':
                    pars[k].set(max=self.parsMax[k])
#        print(pars)
        rez=lmfit.minimize(residuals, pars, args=(dataX, dataY, w), method=method)
#        print(rez.params)
        self.params.update(rez.params.valuesdict())
        self.evaluateFunction()
        dataY=np.array(dataY)
        self.r2=1-np.sum(rez.residual**2)/np.sum((dataY-dataY.mean())**2)
#        self.expType=data[0].type
        self.ycol=ycol
    
    def plotOnIntervalPoints(self, intervals, xcol=0, ax=None, color='k'):
        lines=[]
        if not ax:
            ax=plt.subplot(111)
        if not isinstance(intervals[0], list):
            intervals=[intervals]
        intervals=intervals[0:len(self.vars)]
        ii=list(range(len(intervals)))
        ii.remove(xcol)
        intervals=createMesh(intervals, xcol)
        nc=len(intervals[ii[0]]) if ii else len(intervals[0])
        for i in range(nc):
            xx=[]
            for iii in ii:
                xx.append(intervals[iii][i])
            yy=[]
            for j in intervals[xcol]:
                xxx=list(xx)
                xxx.insert(xcol, j)
                yy.append(self.function(*xxx))
#            yy=[self.function() for p in zip(*intervals)]
            lines.append(ax.plot(intervals[xcol], yy, color)[0])
        return lines

    def plotOnDataPoints(self, data, xcol=0, ax=None, sortByX=1, color='k'):
        xcols=[]
        for v in self.vars:
            xcols.append(int(v[1:])-1)
        if not isinstance(data, list):
            data=[data]
        lines=[]
        if not ax:
            ax=plt.subplot(111)
        for d in data:
            dataY=[self.function(*p) for p in zip(*d.getCols(xcols))]
            lines.append(ax.plot(d[xcol], dataY, color)[0])
            if sortByX:
                dd=np.array(list(zip(*lines[-1].get_data())), dtype=[('x', np.float32),\
                            ('y', np.float32)])
                dd.sort(order='x')
                lines[-1].set_data([dd['x'], dd['y']])
        return lines
    
    def dicToSave(self):
        rez={}
        rez['params']=self.params
        rez['parsMin']=self.parsMin
        rez['parsMax']=self.parsMax
        rez['func']=self.form
        rez['comments']=self.comments
        rez['comment']=self.comment
        rez['name']=self.name
#        rez['expType']=self.expType
        rez['expParams']=list(self.expParams)
        rez['ycol']=self.ycol
        return rez
    
    def resumeFromDic(self, d):
        self.params=d['params']
        self.parsMin=d['parsMin']
        self.parsMax=d['parsMax']
        self.form=d['func']
        self.comments=d.get('comments',{})
        self.comment=d.get('comment',{})
        self.name=d['name']
#        self.expType=d.get('expType','')
        self.expParams=d.get('expParams','')
        self.ycol=d.get('ycol', 1)
        self.evaluateFunction()
    
    def copy(self):
        c=abstractModel(self.form)
        c.params=deepcopy(self.params)
        c.comments=deepcopy(self.comments)
        c.comment=deepcopy(self.comment)
        c.parsMax=deepcopy(self.parsMax)
        c.parsMin=deepcopy(self.parsMin)
#        c.expType=deepcopy(self.expType)
        c.ycol=deepcopy(self.ycol)
        c.expParams=deepcopy(list(self.expParams))
        return c
    
    def formulaToPng(self, file=None, fontsize=12, dpi=100):
        reload(gl)
        ss=''
        for c in self.form:
            if c not in ['{', '}']:
                ss+=c
        varDict={}
        for i, v in enumerate(self.expParams):
            v=gl.varSymbols[v]
            varDict['x_{%i}' % (i+1)]=v
        return renderFormula('x%d=' % (self.ycol+1) +ss, file=file, fontsize=fontsize, dpi=dpi, varSymbols=varDict)
            
    
materialDic={
          'props': {},
          'name': "",
          'notes': "",
          'diagrams': [],
          'approximations': []
          }


if __name__=='__main__':
    x=[0,1,2]
    y=[1,2,3]
    e=experimentalData()
    e.type=''
    e['x']=x
    e['y']=y
    f=abstractModel('{A}')
    print(f.params)
    f.evaluateFunction()
    f.approximateData(e)    
