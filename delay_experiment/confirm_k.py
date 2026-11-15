import sys, numpy as np, pandas as pd, time, scipy.stats as st
sys.path.insert(0,'/home/claude/nb6')
from sim6 import load
ns=load(); k=int(sys.argv[1]); XCAP=float(sys.argv[2]) if len(sys.argv)>2 else 0.20
src=open('/home/claude/exp/exp_actuation_delay.py').read()
head=src[:src.index("# ---- sanity: k = 0")]
exec("""
def objective_from_rows(rows):
    p = {r["cls"]: r for r in rows}; sla_min = min(p[c]["sla_hit"] for c in CLS)
    return p["HIGH"]["p95"] + np.mean([p[c]["p95"] for c in CLS]) + 1e5 * max(0.0, SLA_FLOOR - sla_min)
""",ns)
exec(compile(head,'h','exec'),ns)
run_one=ns['run_one']; W_D=ns['W_D']; make_arrivals=ns['make_arrivals']; SIM=ns['SIM']
d=pd.read_csv(f'/home/claude/exp/frontier_k{k}.csv')
pick={}
for p in ('ADAPTIVE_CONST','ADAPTIVE'):
    q=d[(d.policy==p)&(d.off<=XCAP)]; r=q.loc[q.obj.idxmin()]; pick[p]=(float(r.lo),float(r.hi),'I')
N=20; RH=[0.5,0.7,0.85,0.95]
res={p:[] for p in ('BEST_FIXED','ADAPTIVE_CONST','ADAPTIVE')}
for s in range(N):
    per={p:[] for p in res}
    for rho in RH:
        a=make_arrivals(W_D,rho,7000+31*s+int(rho*100),SIM)
        for p in res:
            P={'BEST_FIXED':'CONG'} if p=='BEST_FIXED' else {p:pick[p]}
            per[p].append(run_one(a,p,rho,{**{'BEST_FIXED':'CONG'},**P},k))
    for p in res: res[p].append((np.mean([x['macro'] for x in per[p]]),np.mean([x['off'] for x in per[p]]),np.mean([x['obj'] for x in per[p]])))
R={p:np.array(v) for p,v in res.items()}
ci=lambda x:(x.mean(),st.t.ppf(.975,len(x)-1)*x.std(ddof=1)/np.sqrt(len(x)))
a,c,b=R['ADAPTIVE'],R['ADAPTIVE_CONST'],R['BEST_FIXED']
out=dict(k=k,xcap=XCAP,adapt_cfg=str(pick['ADAPTIVE']),const_cfg=str(pick['ADAPTIVE_CONST']))
for name,arr in (('ADAPT',a),('CONST',c)):
    out[name+'_off']=arr[:,1].mean(); out[name+'_lat_cost_pct']=ci(100*(arr[:,0]/b[:,0]-1))[0]
dl=ci(100*(a[:,0]/c[:,0]-1)); doff=ci(a[:,1]-c[:,1])
out.update(dict(diff_latency_pct=dl[0],diff_latency_ci=dl[1],diff_off=doff[0],diff_off_ci=doff[1]))
pd.DataFrame([out]).to_csv(f'/home/claude/exp/confirm_k{k}.csv',index=False); print(out)
