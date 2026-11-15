import sys, pickle, importlib, numpy as np, pandas as pd, os, time, itertools
sys.path.insert(0,'/home/claude/nb6')
S0='/tmp/claude-0/-home-claude/a2dcfc82-0cf4-5fb0-ac72-9f9115551e02/scratchpad/dev6'
def load():
    st=pickle.load(open(S0+'/state6.pkl','rb'))
    CELLS=importlib.import_module('build52').CELLS
    codes=[c for t,c in CELLS if t=='code']
    ns=dict(st); ns['np']=np; ns['pd']=pd
    exec(compile(codes[8],'sim','exec'),ns)
    exec(compile(open('/home/claude/nb6/ctrl6.py').read(),'ctrl6','exec'),ns)
    return ns
