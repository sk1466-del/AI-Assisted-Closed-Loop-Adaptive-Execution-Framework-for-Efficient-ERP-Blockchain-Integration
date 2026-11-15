# saves the full validation tuning curve (objective vs off-chain share) of every policy for one delay k
import sys, numpy as np, pandas as pd, time
sys.path.insert(0,'/home/claude/nb6')
from sim6 import load
ns=load(); k=int(sys.argv[1])
src=open('/home/claude/exp/exp_actuation_delay.py').read()
head=src[:src.index("# ---- sanity: k = 0")]          # imports, config, simulate_delay, run_one, world
exec("""
def objective_from_rows(rows):
    p = {r["cls"]: r for r in rows}; sla_min = min(p[c]["sla_hit"] for c in CLS)
    return p["HIGH"]["p95"] + np.mean([p[c]["p95"] for c in CLS]) + 1e5 * max(0.0, SLA_FLOOR - sla_min)
""",ns)
exec(compile(head,'h','exec'),ns)
exec("ARR_T = {(rho, i): make_arrivals(W_D, rho, 1000 + 17 * i, SIM) for i, rho in enumerate(TUNE_RHOS)}",ns)
run_one=ns['run_one']; ARR_T=ns['ARR_T']
def ev(pol,P):
    r=[run_one(a,pol,rho,P,k) for (rho,_),a in ARR_T.items()]
    return float(np.mean([x['obj'] for x in r])),float(np.mean([x['off'] for x in r])),float(np.mean([x['macro'] for x in r]))
pairs=[(lo,hi) for lo in ns['GRID_LO_'] for hi in ns['GRID_HI_'] if hi>lo]
rows=[]; t0=time.time()
o,f,m=ev("BEST_FIXED",{"BEST_FIXED":"CONG"}); rows.append(dict(k=k,policy="BEST_FIXED",lo=None,hi=None,obj=o,off=f,macro=m))
for g in pairs:
    o,f,m=ev("FEEDBACK",{"FEEDBACK":g}); rows.append(dict(k=k,policy="FEEDBACK",lo=g[0],hi=g[1],obj=o,off=f,macro=m))
for pol in ("ADAPTIVE_CONST","ADAPTIVE"):
    for g in pairs:
        o,f,m=ev(pol,{pol:(g[0],g[1],"I")}); rows.append(dict(k=k,policy=pol,lo=g[0],hi=g[1],obj=o,off=f,macro=m))
pd.DataFrame(rows).to_csv(f'/home/claude/exp/frontier_k{k}.csv',index=False); print('done',k,time.time()-t0)
