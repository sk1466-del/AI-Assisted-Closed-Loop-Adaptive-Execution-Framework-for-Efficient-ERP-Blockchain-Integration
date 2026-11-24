"""Recompute the key numbers of the manuscript from the released results files and compare.
Usage: python check_numbers.py   (needs pandas, numpy; run from the release folder)

Every section runs inside its own guard: an error in one section (for example a missing
file or column) is reported and counted as a failure, and the remaining sections still run.
The summary and the exit statement are the last lines of the script."""
import pandas as pd, numpy as np, json, sys, os, traceback
H=os.path.dirname(os.path.abspath(__file__)); RES=os.path.join(H,'results'); DEL=os.path.join(H,'delay_experiment')
fails=0; n=0
def chk(name,got,want,tol):
    global fails,n
    n+=1
    got=float(got); ok=bool(np.isfinite(got)) and abs(got-want)<=tol; fails+=0 if ok else 1
    print(('PASS ' if ok else 'FAIL ')+f'{name}: recomputed {got:.4g}, manuscript {want}')
def section(title,fn):
    global fails
    print(f'\n## {title}')
    try: fn()
    except Exception:
        fails+=1; print(f'ERROR in section "{title}" (counted as one failure):'); traceback.print_exc(limit=1)
rd=lambda f: pd.read_csv(os.path.join(RES,f))
def col(df,*keys):
    """First column whose lower-case name contains any of the keys."""
    for k in keys:
        for c in df.columns:
            if k in c.lower(): return c
    raise KeyError(f'no column matching {keys}; columns are {list(df.columns)}')
RHOS=(0.5,0.7,0.85,0.95)

def design_hash():
    global fails,n
    s=json.load(open(os.path.join(RES,'RESULTS_SUMMARY.json'))); n+=1
    ok=s['config_hash']=='d6c30b92b47d5336'; fails+=0 if ok else 1
    print(('PASS ' if ok else 'FAIL ')+f"design hash: {s['config_hash']} (manuscript: d6c30b92b47d5336)")

def table2a():
    b=rd('table_prediction_B.csv').set_index('Model')
    for m,w in (('GradientBoosting',258.1),('Baseline: train mean',331.5),('Baseline: persistence (5-block mean)',339.3),('Baseline: 36-block mean',300.9),('Baseline: hour-of-day mean',294.9)): chk('Table 2A test MAE '+m,b.loc[m,'test_MAE'],w,0.06)
    chk('Forecast test R2 (gradient boosting)',b.loc['GradientBoosting','test_R2'],0.39,0.006)
    bb=rd('table_prediction_block_bootstrap.csv'); bb=bb[bb.task.str.startswith('B')].set_index('vs')
    for m,w in (('Baseline: train mean',22.1),('Baseline: persistence (5-block mean)',23.9),('Baseline: 36-block mean',14.2),('Baseline: hour-of-day mean',12.5)): chk('Table 2A MAE gain vs '+m,bb.loc[m,'MAE_improvement_pct'],w,0.06)

def table2b():
    mp=rd('table_matched_pairs.csv')
    for c,k in (('ADAPTIVE_CONST',4),('ADAPTIVE_SHUFFLED',8),('FEEDBACK',5)): chk(f'Table 2B matched pairs {c}',int(mp[mp.comparator==c].matched.sum()),k,0)

def table3a():
    f=rd('table_fairness.csv')
    W={'STATIC':[0.981,0.896,0.570,0.108],'PRIO_ONLY':[0.948,0.780,0.424,0.072],'BEST_FIXED':[0.986,0.970,0.948,0.924],'ADAPTIVE':[0.981,0.969,0.947,0.924]}
    for p,v in W.items():
        for r,w in zip(RHOS,v): chk(f'Table 3A worst-class SLA {p} rho={r}',f[(f.rho==r)&(f.policy==p)].min_class_SLA.iloc[0],w,0.0006)
    raw=rd('sim_raw_results.csv'); a=raw[raw.cls=='ALL']
    T={'STATIC':[0.1,5.5,38.4,88.7],'PRIO_ONLY':[0.1,5.4,38.3,88.6],'BEST_FIXED':[0.0,0.3,1.0,2.5]}
    for p,v in T.items():
        for r,w in zip(RHOS,v): chk(f'Table 3A time overloaded % {p} rho={r}',a[(a.rho==r)&(a.policy==p)].frac_time_overloaded.mean()*100,w,0.06)

def table3b():
    pw=rd('table_pairwise_comparisons.csv'); pw=pw[(pw.A=='ADAPTIVE')&(pw.B=='BEST_FIXED')]
    W3={0.5:(39.1,-4.1,-8.8),0.7:(3.9,-0.7,-1.0),0.85:(0.4,-0.1,-0.1),0.95:(0.05,0.0,0.0)}
    for r,(o,m,l) in W3.items():
        q=pw[pw.rho==r].set_index('metric').improvement_pct
        chk(f'Table 3B off-chain reduction rho={r}',q['offload'],o,0.06)
        chk(f'Table 3B class-averaged p95 latency improvement rho={r}',q['macro_p95'],m,0.06)
        chk(f'Table 3B LOW p95 latency improvement rho={r}',q['low_p95'],l,0.06)

def table4a():
    ov=rd('table_completed_tps_overload.csv')
    W4={(1.0,'STATIC'):(0.966,0.02,44921),(1.0,'BEST_FIXED'):(1.000,0.91,8),(1.0,'ADAPTIVE'):(1.000,0.91,8),(1.0,'FEEDBACK'):(1.000,0.89,5),
        (1.1,'STATIC'):(0.879,0.00,176290),(1.1,'BEST_FIXED'):(1.000,0.87,16),(1.1,'ADAPTIVE'):(1.000,0.87,16),(1.1,'FEEDBACK'):(1.000,0.84,37),
        (1.25,'STATIC'):(0.774,0.00,377519),(1.25,'BEST_FIXED'):(1.000,0.75,22),(1.25,'ADAPTIVE'):(1.000,0.75,22),(1.25,'FEEDBACK'):(1.000,0.72,38)}
    for (l,p),(cr,sla,bl) in W4.items():
        q=ov[(ov.load==l)&(ov.policy==p)].iloc[0]
        chk(f'Table 4A completed/arrived {p} load={l}',q.completed_to_arrived_ratio,cr,0.0006); chk(f'Table 4A worst-class SLA {p} load={l}',q.min_class_SLA,sla,0.006); chk(f'Table 4A final backlog {p} load={l}',q.backlog_final,bl,0.6)

def table4b():
    bu=rd('table_bursty.csv'); bu=bu[bu.rho_base==0.6]
    for sc,pol,p95,rec,off in (('S1','STATIC',14848,33.4,0.00),('S1','BEST_FIXED',4521,2.5,0.43),('S1','ADAPTIVE',4557,2.6,0.38),('S2','STATIC',19858,45.1,0.00),('S2','BEST_FIXED',2718,0.0,0.43),('S2','ADAPTIVE',2723,0.0,0.38)):
        q=bu[bu.scenario.str.startswith(sc)&(bu.policy==pol)].iloc[0]
        chk(f'Table 4B {sc} {pol} in-event p95',q.window_macro_p95,p95,1.0); chk(f'Table 4B {sc} {pol} recovery',q.recovery_blocks,rec,0.06); chk(f'Table 4B {sc} {pol} off-chain share',q.offchain_share,off,0.006)

def table_s6_offchain():
    # Off-chain reduction of ADAPTIVE vs BEST_FIXED per bursty scenario (Sec. 4.3, Conclusion, Supp. Tables S2 and S6)
    bu=rd('table_bursty.csv'); red={}
    for rb in (0.3,0.6):
        d=bu[bu.rho_base==rb]
        for sc in sorted(d.scenario.unique()):
            g=d[d.scenario==sc].set_index('policy').offchain_share
            if 'ADAPTIVE' in g and 'BEST_FIXED' in g:
                red[(rb,sc)]=(g['BEST_FIXED']-g['ADAPTIVE'])/g['BEST_FIXED']*100
                print(f'   info: base rho={rb} {sc}: off-chain reduction {red[(rb,sc)]:.2f} %')
    r3=[v for (rb,_),v in red.items() if rb==0.3]; r6=[v for (rb,_),v in red.items() if rb==0.6]
    chk('Table S6 off-chain reduction, base 0.3, max (Conclusion 89 %; Table S2 89.4 %)',max(r3),89.4,0.06)
    chk('Table S6 off-chain reduction, base 0.3, min (Sec. 4.3: 86 %)',min(r3),86,0.5)
    chk('Table 4B off-chain reduction, base 0.6, min (Sec. 4.3: 11 %)',min(r6),11,0.5)
    chk('Table 4B off-chain reduction, base 0.6, max (Sec. 4.3: 13 %)',max(r6),13,0.5)

def table4c():
    dp=rd('table_capacity_dip.csv'); dp=dp[dp.capacity_during_dip==0.4]
    for rho,pol,p95,sla,pk,rec in ((0.5,'STATIC',9545,0.94,1741,9.1),(0.5,'BEST_FIXED',2774,0.98,640,0.0),(0.5,'ADAPTIVE',2912,0.97,679,0.1),(0.7,'STATIC',18307,0.81,3393,58.4),(0.7,'BEST_FIXED',5557,0.94,1441,2.6),(0.7,'ADAPTIVE',5590,0.94,1441,2.6)):
        q=dp[(dp.rho==rho)&(dp.policy==pol)].iloc[0]
        chk(f'Table 4C {pol} rho={rho} in-event p95',q.window_macro_p95,p95,1.0); chk(f'Table 4C {pol} rho={rho} min-class SLA',q.min_class_SLA,sla,0.006); chk(f'Table 4C {pol} rho={rho} peak backlog',q.backlog_max,pk,1.0); chk(f'Table 4C {pol} rho={rho} recovery',q.recovery_blocks,rec,0.06)

def table5a():
    # LOW starvation rate and maximum LOW wait for every policy at all four loads
    f=rd('table_fairness.csv')
    S={'STATIC':[0.000,0.000,0.108,0.741],'PRIO_ONLY':[0.000,0.005,0.142,0.777],'BEST_FIXED':[0.0]*4,'FEEDBACK':[0.0]*4,'ADAPTIVE':[0.0]*4}
    M={'STATIC':[8103,11668,25763,110708],'PRIO_ONLY':[9336,13328,27557,112264],'BEST_FIXED':[9056,9537,9702,9994],'FEEDBACK':[9149,9420,9846,10091],'ADAPTIVE':[9218,9491,9723,9994]}
    for p in S:
        for i,r in enumerate(RHOS):
            q=f[(f.rho==r)&(f.policy==p)].iloc[0]
            chk(f'Table 5A LOW starvation rate {p} rho={r}',q.LOW_starvation,S[p][i],0.0006)
            chk(f'Table 5A max LOW wait {p} rho={r}',q.LOW_max_wait,M[p][i],1.0)

def table5b():
    sr=pd.read_csv(os.path.join(RES,'table_sensitivity_ranges.csv'),header=[0,1],index_col=0)
    W5={0.5:{'offchain_saving_pct':(24.8,46.1),'macro_p95_cost_pct':(1.07,6.98),'LOW_p95_cost_pct':(3.05,15.84),'HIGH_p95_cost_pct':(0.0,0.28)},
        0.7:{'offchain_saving_pct':(2.26,5.41),'macro_p95_cost_pct':(0.23,0.91),'LOW_p95_cost_pct':(0.28,1.87),'HIGH_p95_cost_pct':(-0.01,0.07)},
        0.85:{'offchain_saving_pct':(0.24,0.66),'macro_p95_cost_pct':(-0.05,0.33),'LOW_p95_cost_pct':(-0.16,0.55),'HIGH_p95_cost_pct':(0.0,0.02)}}
    for l,d in W5.items():
        for c,(lo,hi) in d.items():
            chk(f'Table 5B {c} min load={l}',float(sr.loc[l,(c,'min')]),lo,0.06); chk(f'Table 5B {c} max load={l}',float(sr.loc[l,(c,'max')]),hi,0.06)

def table6():
    W6={0:[0.7,0.0,-0.2,-0.2],2:[2.0,-0.1,-0.7,0.1],5:[1.9,-0.4,-0.5,0.0],10:[2.7,-1.5,-0.9,0.1]}
    for k,v in W6.items():
        d=pd.read_csv(os.path.join(DEL,f'frontier_k{k}.csv')); bm=d[d.policy=='BEST_FIXED'].macro.iloc[0]
        for cap,w in zip((0.20,0.25,0.30,0.35),v):
            e=lambda p: d[(d.policy==p)&(d.off<=cap)].macro.min()
            chk(f'Table 6 forecast latency improvement k={k} cap={cap}',(e('ADAPTIVE_CONST')-e('ADAPTIVE'))/bm*100,w,0.06)

def table_s2_divergence():
    # Share of blocks in which ADAPTIVE chooses a different regime from the no-forecast variant (Sec. 4.1, Table S2)
    dd=rd('table_decision_divergence.csv'); rc=col(dd,'rho','load')
    vc=[c for c in dd.columns if c!=rc and pd.api.types.is_numeric_dtype(dd[c]) and any(k in c.lower() for k in ('diverg','differ','pct','frac','share'))]
    if not vc: raise KeyError(f'no divergence column; columns are {list(dd.columns)}')
    vc=vc[0]; scale=100 if dd[vc].max()<=1 else 1
    print(f'   info: using columns {rc!r} and {vc!r} (x{scale})')
    for r,w in zip(RHOS,(21.8,8.7,1.1,0.1)): chk(f'Table S2 decision divergence rho={r}',dd[np.isclose(dd[rc],r)][vc].iloc[0]*scale,w,0.06)

def table_s6b():
    bp=rd('table_bursty_paired.csv')
    x=bp[(bp.rho_base==0.6)&(bp.comparator=='BEST_FIXED')&(bp.metric=='window_macro_p95')&bp.scenario.str.contains('announced')&bp.scenario.str.startswith('S2')].iloc[0]
    chk('Table S6b month-end rho=0.6 latency improvement',x.a_better_by,-0.20,0.01); chk('Table S6b month-end rho=0.6 CI half-width',x.ci95,0.29,0.01)

for t,fn in (('Design hash',design_hash),('Table 2A',table2a),('Table 2B',table2b),('Table 3A',table3a),('Table 3B',table3b),
             ('Table 4A',table4a),('Table 4B',table4b),('Off-chain reductions (Table 4B, Supp. Table S6)',table_s6_offchain),
             ('Table 4C',table4c),('Table 5A',table5a),('Table 5B',table5b),('Table 6',table6),
             ('Supp. Table S2 decision divergence',table_s2_divergence),('Supp. Table S6b',table_s6b)):
    section(t,fn)

# Summary and exit: keep these as the last lines so that every check above is executed.
print(f'\nCHECKS RUN: {n}   FAILED: {fails}')
sys.exit(1 if fails else 0)
