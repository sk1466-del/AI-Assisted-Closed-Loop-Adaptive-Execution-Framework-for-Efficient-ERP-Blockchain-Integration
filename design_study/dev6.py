import sys, os, pickle, time, itertools, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/nb6')
from sim6 import load, S0
from multiprocessing import Pool
ns = load(); g = ns
SIM=ns['SIM']; CLS=ns['CLS']; df=ns['df']; SL=ns['SL']; TB=ns['TB']
# ---- forecasts on validation: mean (selected model) and q80 (uncertainty-aware) ----
def forecasts():
    f = S0 + '/q80.pkl'
    if os.path.exists(f): return pickle.load(open(f,'rb'))
    from sklearn.pipeline import Pipeline; from sklearn.preprocessing import StandardScaler; from sklearn.ensemble import GradientBoostingRegressor
    X = df[ns['FEATURES_DEM']]; y = df[ns['TARGET_DEM']]
    m = Pipeline([("sc",StandardScaler()),("m",GradientBoostingRegressor(loss="quantile",alpha=0.8,n_estimators=300,learning_rate=0.03,max_depth=3,random_state=ns['SEED']))])
    m.fit(X.iloc[SL['tr']], y.iloc[SL['tr']])
    out = dict(mean_va=TB['fitted'][TB['SEL']].predict(X.iloc[SL['va']]), q80_va=m.predict(X.iloc[SL['va']]), y_va=y.iloc[SL['va']].values, q80_model=m)
    pickle.dump(out, open(f,'wb')); return out
FQ = forecasts()
cov = float((FQ['y_va'] <= FQ['q80_va']).mean()); print("q80 coverage on validation:", round(cov,3), flush=True)
RATIO = float(FQ['q80_va'].mean() / FQ['mean_va'].mean())
W = ns['make_world6'](SL['va'], {'mean': FQ['mean_va'], 'q80': FQ['q80_va'], 'meanx': FQ['mean_va'] * RATIO})
W['rel_hat']['const'] = np.ones(len(W['dt']))
ARR = {(rho, i): ns['make_arrivals'](W, rho, 1000 + 17 * i + 0, SIM) for i, rho in enumerate(ns['TUNE_RHOS'])}
def objective(rows):
    p = {r["cls"]: r for r in rows}; sla_min = min(p[c]["sla_hit"] for c in CLS)
    return p["HIGH"]["p95"] + np.mean([p[c]["p95"] for c in CLS]) + 1e5 * max(0.0, ns['SLA_FLOOR'] - sla_min)
def tune_eval(args):
    pol, P = args; o, f = [], []
    for (rho, _), arr in ARR.items():
        res = ns['simulate6'](arr, W, pol, rho, SIM, P); rows, gl = ns['summarize'](res, SIM)
        o.append(objective(rows)); f.append(1 - gl['onchain_units_per_tx'])
    return float(np.mean(o)), float(np.mean(f))
def configs():
    C = []
    pairs = [(lo, hi) for lo in [0.0,0.2,0.4,0.8] for hi in [0.6,1.0,1.5,2.5] if hi > lo]
    for (lo,hi),dl,dw,uq,mode in itertools.product(pairs,[0.0,0.2,0.4],[0,3,8],['mean','q80'],['I','H']):
        C.append(('HR', dict(lo=lo,hi=hi,delta=dl,dwell=dw,uq=uq,mode=mode,guard=None)))
    for H,b,uq in itertools.product([2,4,6,12],[0.25,0.5,1,2,4,8],['mean','q80']):
        C.append(('MPC', dict(H=H,bmax=b,uq=uq)))
    return C
def configs2():
    C = []
    pairs = [(lo, hi) for lo in [0.0,0.2,0.4,0.8] for hi in [0.6,1.0,1.5,2.5] if hi > lo]
    for (lo,hi),dl,dw,mode in itertools.product(pairs,[0.0,0.2,0.4],[0,3,8],['I','H']):
        C.append(('HR', dict(lo=lo,hi=hi,delta=dl,dwell=dw,uq='meanx',mode=mode,guard=None)))
    for H,b,uq in itertools.product([1,2,4,6,12],[0.02,0.05,0.1,0.25],['mean','q80','meanx']):
        C.append(('MPC', dict(H=H,bmax=b,uq=uq)))
    return C
def configs3():
    C = []
    pairs = [(lo, hi) for lo in [0,.1,.2,.3,.4,.5,.6,.8,1.0] for hi in [.4,.6,.8,1.0,1.25,1.5,2.0,2.5] if hi > lo]
    for (lo,hi),(dl,dw),uq in itertools.product(pairs,[(0,0),(0.2,0),(0,3),(0.2,3)],['none','const','mean']):
        C.append(('HR', dict(lo=float(lo),hi=float(hi),delta=dl,dwell=dw,uq=uq,mode='I',guard=None)))
    return C
if __name__ == '__main__':
    stage = sys.argv[1]
    if stage == 'tune3':
        C = configs3(); t0=time.time()
        with Pool(2) as p: R = p.map(tune_eval, C, chunksize=4)
        rows = [dict(policy=c[0], **c[1], obj=r[0], offload=r[1]) for c,r in zip(C,R)]
        pd.DataFrame(rows).to_csv(S0+'/tune6c.csv', index=False); print('tuned3', len(C), 'configs in', round(time.time()-t0), 's')
    if stage == 'tune2':
        C = configs2(); t0=time.time()
        with Pool(2) as p: R = p.map(tune_eval, C, chunksize=4)
        rows = [dict(policy=c[0], **c[1], obj=r[0], offload=r[1]) for c,r in zip(C,R)]
        pd.DataFrame(rows).to_csv(S0+'/tune6b.csv', index=False); print('tuned2', len(C), 'configs in', round(time.time()-t0), 's')
    if stage == 'tune':
        C = configs(); t0=time.time()
        with Pool(2) as p: R = p.map(tune_eval, C, chunksize=4)
        rows = [dict(policy=c[0], **c[1], obj=r[0], offload=r[1]) for c,r in zip(C,R)]
        pd.DataFrame(rows).to_csv(S0+'/tune6.csv', index=False); print('tuned', len(C), 'configs in', round(time.time()-t0), 's')
