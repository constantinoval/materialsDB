import json
from collections import defaultdict
class myDD(defaultdict):
    def __missing__(self, key):
        return key

#class varDefsconfig:
#      def __init__(self):
#          self.readConfig()
#      def readConfig(self):
d=json.load(open('varDefs.json'))
ttN=d['ttN']
names=myDD(lambda: '', d['names'])
varSymbols=myDD(lambda: '', d['varSymbols'])
matCompletions=d['matCompletions']
