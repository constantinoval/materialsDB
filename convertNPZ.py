import os
import numpy as np
filesList=os.listdir(os.curdir)
diags=[]
for f in filesList:
    if (f[-4:]=='.npz') and (not 'dov' in f):
        diags.append(f)
for f in diags:
    print(f)
    d=np.load(f)
    ddov=None
    if os.path.exists(f[:-4]+'-dov.npz'):
        ddov=np.load(f[:-4]+'-dov.npz')
    etype=f[0]
    T=float(f.split('-')[-1][:-4])+273
    with open(f[:-4]+'.txt', 'w') as txt:
        txt.write(etype+'\n')
        txt.write('ep s de T')
        if ddov:
            txt.write(' eperr serr deerr')
        txt.write('\n')
        for i in range(len(d['e'])):
            txt.write('{} {} {} '.format(d['e'][i], d['s'][i], d['de'][i]))
            txt.write(str(T))
            if ddov:
                txt.write(' {} {} {}'.format(ddov['e'][i], ddov['s'][i], ddov['de'][i]))
            txt.write('\n')
            