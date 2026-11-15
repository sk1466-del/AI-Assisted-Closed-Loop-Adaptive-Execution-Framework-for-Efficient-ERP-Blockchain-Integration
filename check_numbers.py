"""Recompute the key numbers of the manuscript from the released results files and compare.
Usage: python check_numbers.py   (needs pandas, numpy; run from the release folder)"""
import pandas as pd, numpy as np, json, sys, os
H=os.path.dirname(os.path.abspath(__file__)); RES=os.path.join(H,'results'); DEL=os.path.join(H,'delay_experiment')
fails=0
def chk(name,got,want,tol):
    global fails
    ok=abs(got-want)<=tol; fails+=0 if ok else 1
    print(('PASS ' if ok else 'FAIL ')+f'{name}: recomputed {got:.4g}, manuscript {want}')
rd=lambda f: pd.read_csv(os.path.join(RES,f))
s=json.load(open(os.path.join(RES,'RESULTS_SUMMARY.json')))
print('design hash:',s['config_hash'], '(manuscript: d6c30b92b47d5336)'); fails+= s['config_hash']!='d6c30b92b47d5336'
# Table 2A: forecast accuracy (test MAE) and block-bootstrap gains
b=rd('table_prediction_B.csv').set_index('Model')
for m,w in (('GradientBoosting',258.1),('Baseline: train mean',331.5),('Baseline: persistence (5-block mean)',339.3),('Baseline: 36-block mean',300.9),('Baseline: hour-of-day mean',294.9)): chk('Table 2A test MAE '+m,b.loc[m,'test_MAE'],w,0.06)
chk('Forecast test R2 (gradient boosting)',b.loc['GradientBoosting','test_R2'],0.39,0.006)
bb=rd('table_prediction_block_bootstrap.csv'); bb=bb[bb.task.str.startswith('B')].set_index('vs')
for m,w in (('Baseline: train mean',22.1),('Baseline: persistence (5-block mean)',23.9),('Baseline: 36-block mean',14.2),('Baseline: hour-of-day mean',12.5)): chk('Table 2A MAE gain vs '+m,bb.loc[m,'MAE_improvement_pct'],w,0.06)
# Table 3A and 5A: fairness table; time overloaded from sim_raw_results
f=rd('table_fairness.csv')
W={'STATIC':[0.981,0.896,0.570,0.108],'PRIO_ONLY':[0.948,0.780,0.424,0.072],'BEST_FIXED':[0.986,0.970,0.948,0.924],'ADAPTIVE':[0.981,0.969,0.947,0.924]}
for p,v in W.items():
    for r,w in zip((0.5,0.7,0.85,0.95),v): chk(f'Table 3A worst-class SLA {p} rho={r}',f[(f.rho==r)&(f.policy==p)].min_class_SLA.iloc[0],w,0.0006)
raw=rd('sim_raw_results.csv'); a=raw[raw.cls=='ALL']
T={'STATIC':[0.1,5.5,38.4,88.7],'PRIO_ONLY':[0.1,5.4,38.3,88.6],'BEST_FIXED':[0.0,0.3,1.0,2.5]}
for p,v in T.items():
    for r,w in zip((0.5,0.7,0.85,0.95),v): chk(f'Table 3A time overloaded % {p} rho={r}',a[(a.rho==r)&(a.policy==p)].frac_time_overloaded.mean()*100,w,0.06)
# Table 3B
pw=rd('table_pairwise_comparisons.csv'); pw=pw[(pw.A=='ADAPTIVE')&(pw.B=='BEST_FIXED')]
W3={0.5:(39.1,-4.1,-8.8),0.7:(3.9,-0.7,-1.0),0.85:(0.4,-0.1,-0.1),0.95:(0.05,0.0,0.0)}
for r,(o,m,l) in W3.items():
    q=pw[pw.rho==r].set_index('metric').improvement_pct
    chk(f'Table 3B off-chain reduction rho={r}',q['offload'],o,0.06); chk(f'Table 3B class-avg p95 change rho={r}',q['macro_p95'],m,0.06); chk(f'Table 3B LOW p95 change rho={r}',q['low_p95'],l,0.06)
# Table 4B bursty (base 0.6) and 4C capacity dip 40 %
bu=rd('table_bursty.csv'); bu=bu[bu.rho_base==0.6]
for sc,pol,p95,rec,off in (('S1','STATIC',14848,33.4,0.00),('S1','BEST_FIXED',4521,2.5,0.43),('S1','ADAPTIVE',4557,2.6,0.38),('S2','STATIC',19858,45.1,0.00),('S2','BEST_FIXED',2718,0.0,0.43),('S2','ADAPTIVE',2723,0.0,0.38)):
    q=bu[bu.scenario.str.startswith(sc)&(bu.policy==pol)].iloc[0]
    chk(f'Table 4B {sc} {pol} in-event p95',q.window_macro_p95,p95,1.0); chk(f'Table 4B {sc} {pol} recovery',q.recovery_blocks,rec,0.06); chk(f'Table 4B {sc} {pol} off-chain share',q.offchain_share,off,0.006)
dp=rd('table_capacity_dip.csv'); dp=dp[dp.capacity_during_dip==0.4]
for rho,pol,p95,sla,pk,rec in ((0.5,'STATIC',9545,0.94,1741,9.1),(0.5,'BEST_FIXED',2774,0.98,640,0.0),(0.5,'ADAPTIVE',2912,0.97,679,0.1),(0.7,'STATIC',18307,0.81,3393,58.4),(0.7,'BEST_FIXED',5557,0.94,1441,2.6),(0.7,'ADAPTIVE',5590,0.94,1441,2.6)):
    q=dp[(dp.rho==rho)&(dp.policy==pol)].iloc[0]
    chk(f'Table 4C {pol} rho={rho} in-event p95',q.window_macro_p95,p95,1.0); chk(f'Table 4C {pol} rho={rho} min-class SLA',q.min_class_SLA,sla,0.006); chk(f'Table 4C {pol} rho={rho} peak backlog',q.backlog_max,pk,1.0); chk(f'Table 4C {pol} rho={rho} recovery',q.recovery_blocks,rec,0.06)
# Table 5A (LOW starvation, max wait)
for r,p,lw in ((0.5,'ADAPTIVE',9218),(0.7,'STATIC',11668),(0.7,'PRIO_ONLY',13328),(0.7,'ADAPTIVE',9491),(0.85,'STATIC',25763),(0.95,'PRIO_ONLY',112264)): chk(f'Table 5A max LOW wait {p} rho={r}',f[(f.rho==r)&(f.policy==p)].LOW_max_wait.iloc[0],lw,1.0)
# Table 6: delayed activation, lower envelope of class-averaged p95 over grid points with off-chain share <= cap
W6={0:[0.7,0.0,-0.2,-0.2],2:[2.0,-0.1,-0.7,0.1],5:[1.9,-0.4,-0.5,0.0],10:[2.7,-1.5,-0.9,0.1]}
for k,v in W6.items():
    d=pd.read_csv(os.path.join(DEL,f'frontier_k{k}.csv')); bm=d[d.policy=='BEST_FIXED'].macro.iloc[0]
    for cap,w in zip((0.20,0.25,0.30,0.35),v):
        e=lambda p: d[(d.policy==p)&(d.off<=cap)].macro.min()
        chk(f'Table 6 forecast advantage k={k} cap={cap}',(e('ADAPTIVE_CONST')-e('ADAPTIVE'))/bm*100,w,0.06)
# Table 4A overload (three seeds)
ov=rd('table_completed_tps_overload.csv')
W4={(1.0,'STATIC'):(0.966,0.02,44921),(1.0,'BEST_FIXED'):(1.000,0.91,8),(1.0,'ADAPTIVE'):(1.000,0.91,8),(1.0,'FEEDBACK'):(1.000,0.89,5),
    (1.1,'STATIC'):(0.879,0.00,176290),(1.1,'BEST_FIXED'):(1.000,0.87,16),(1.1,'ADAPTIVE'):(1.000,0.87,16),(1.1,'FEEDBACK'):(1.000,0.84,37),
    (1.25,'STATIC'):(0.774,0.00,377519),(1.25,'BEST_FIXED'):(1.000,0.75,22),(1.25,'ADAPTIVE'):(1.000,0.75,22),(1.25,'FEEDBACK'):(1.000,0.72,38)}
for (l,p),(cr,sla,bl) in W4.items():
    q=ov[(ov.load==l)&(ov.policy==p)].iloc[0]
    chk(f'Table 4A completed/arrived {p} load={l}',q.completed_to_arrived_ratio,cr,0.0006); chk(f'Table 4A worst-class SLA {p} load={l}',q.min_class_SLA,sla,0.006); chk(f'Table 4A final backlog {p} load={l}',q.backlog_final,bl,0.6)
# Table 5B sensitivity ranges (min, max over the varied assumptions)
sr=pd.read_csv(os.path.join(RES,'table_sensitivity_ranges.csv'),header=[0,1],index_col=0)
W5={0.5:{'offchain_saving_pct':(24.8,46.1),'macro_p95_cost_pct':(1.07,6.98),'LOW_p95_cost_pct':(3.05,15.84),'HIGH_p95_cost_pct':(0.0,0.28)},
    0.7:{'offchain_saving_pct':(2.26,5.41),'macro_p95_cost_pct':(0.23,0.91),'LOW_p95_cost_pct':(0.28,1.87),'HIGH_p95_cost_pct':(-0.01,0.07)},
    0.85:{'offchain_saving_pct':(0.24,0.66),'macro_p95_cost_pct':(-0.05,0.33),'LOW_p95_cost_pct':(-0.16,0.55),'HIGH_p95_cost_pct':(0.0,0.02)}}
for l,d in W5.items():
    for col,(lo,hi) in d.items():
        chk(f'Table 5B {col} min load={l}',float(sr.loc[l,(col,'min')]),lo,0.06); chk(f'Table 5B {col} max load={l}',float(sr.loc[l,(col,'max')]),hi,0.06)
print('\nFAILED CHECKS:',fails); sys.exit(1 if fails else 0)

# Table 5A rho=0.7 starvation and SLA
for p,sv in (('STATIC',0.0005),('PRIO_ONLY',0.005),('ADAPTIVE',0.0)): chk(f'Table 5A LOW starvation {p} rho=0.7',f[(f.rho==0.7)&(f.policy==p)].LOW_starvation.iloc[0],sv,0.0006)
# Table 2B: number of matched pairs per comparator (Supplementary Table S5b)
mp=rd('table_matched_pairs.csv')
for c,n in (('ADAPTIVE_CONST',4),('ADAPTIVE_SHUFFLED',8),('FEEDBACK',5)): chk(f'Table 2B matched pairs {c}',int(mp[mp.comparator==c].matched.sum()),n,0)
# Supplementary Table S6b: paired CIs, base rho 0.6 month-end announced and 0.3 order bursts
bp=rd('table_bursty_paired.csv')
x=bp[(bp.rho_base==0.6)&(bp.comparator=='BEST_FIXED')&(bp.metric=='window_macro_p95')&bp.scenario.str.contains('announced')&bp.scenario.str.startswith('S2')].iloc[0]
chk('Table S6b month-end rho=0.6 gain',x.a_better_by,-0.20,0.01); chk('Table S6b month-end rho=0.6 CI',x.ci95,0.29,0.01)
