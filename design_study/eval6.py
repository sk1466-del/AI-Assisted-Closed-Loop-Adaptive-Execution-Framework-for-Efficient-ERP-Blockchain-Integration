import sys, os, pickle, time, itertools, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/nb6')
import dev6
from dev6 import *
from multiprocessing import Pool
OLD = ns['tune_df']; T1 = pd.read_csv(S0+'/tune6.csv'); T2 = pd.read_csv(S0+'/tune6b.csv'); T3 = pd.read_csv(S0+'/tune6c.csv'); T = pd.concat([T1, T2, T3], ignore_index=True)
TUNED = ns['TUNED']
W['rel_hat']['ADAPTIVE'] = W['rel_hat']['mean']
Ls = min(OLD[OLD.key.isin(['BEST_FIXED','FEEDBACK','ADAPTIVE','ADAPTIVE_CONST'])].obj.min(), T.obj.min())
def pick(d):
    ok = d[d.obj <= 1.05 * Ls]
    return (ok.sort_values(['offload','obj']).iloc[0], True) if len(ok) else (d.sort_values('obj').iloc[0], False)
def hr_row(d):
    r, ok = pick(d); return ('HR', dict(lo=float(r.lo),hi=float(r.hi),delta=float(r.delta),dwell=int(r.dwell),uq=r.uq,mode=r['mode'],guard=None)), r, ok
hr = T[T.policy=='HR']; mp = T[T.policy=='MPC']
VAR = {}
VAR['STATIC'] = ('STATIC', {}); VAR['PRIO_ONLY'] = ('PRIO_ONLY', {}); VAR['BEST_FIXED'] = ('BEST_FIXED', TUNED)
VAR['FEEDBACK_v5'] = ('FEEDBACK', TUNED); VAR['ADAPTIVE_v5'] = ('ADAPTIVE', TUNED)
info = {}
def add(name, d):
    r, ok = pick(d); VAR[name] = ('HR', dict(lo=float(r.lo),hi=float(r.hi),delta=float(r.delta),dwell=int(r.dwell),uq=r.uq,mode=r['mode'],guard=None)); info[name] = (r, ok)
f = T3
add('FEEDBACK_fine', f[(f.uq=='none')&(f.delta==0)&(f.dwell==0)])
add('CONST_fine', f[(f.uq=='const')&(f.delta==0)&(f.dwell==0)])
add('ADAPT_fine', f[(f.uq=='mean')&(f.delta==0)&(f.dwell==0)])
add('ADAPT_fine_hyst', f[(f.uq=='mean')&(f.delta>0)&(f.dwell==0)])
add('ADAPT_fine_dwell', f[(f.uq=='mean')&(f.delta==0)&(f.dwell>0)])
add('ADAPT_fine_hyst_dwell', f[(f.uq=='mean')&(f.delta>0)&(f.dwell>0)])
add('ADAPT_q80', hr[(hr.uq=='q80')&(hr.delta==0)&(hr.dwell==0)])
add('ADAPT_meanx', hr[(hr.uq=='meanx')&(hr.delta==0)&(hr.dwell==0)])
for name, d in [('MPC', mp)]:
    r, ok = pick(d); VAR[name] = ('MPC', dict(H=int(r.H), bmax=float(r.bmax), uq=r.uq)); info[name] = (r, ok)
p = dict(VAR['ADAPT_fine'][1]); p['guard'] = 0.6; VAR['ADAPT_fine_guard'] = ('HR', p)
print('L* =', round(Ls,1))
for k, (r, ok) in info.items(): print(f"{k:16s} within_eps={ok}  obj={r.obj:.0f} offload={r.offload:.3f}  cfg={VAR[k][1]}")
sys.stdout.flush()
def starv(res, S):
    m = res['arr_t'] >= res['t_warm']; lat = res['lat'][m]; cl = res['cls'][m]
    um = res['q_t'] >= res['t_warm']; ua = res['t_end'] - res['q_t'][um]; uc = res['q_c'][um]
    n_low = (cl == 2).sum() + (uc == 2).sum()
    return (((lat[cl == 2] > 3 * S['SLA']).sum() + (ua[uc == 2] > 3 * S['SLA']).sum()) / max(n_low, 1))
def metrics_of(res, rows, gl):
    p = {r['cls']: r for r in rows}
    return dict(obj=objective(rows), macro_p95=np.mean([p[c]['p95'] for c in CLS]), high_p95=p['HIGH']['p95'], low_p95=p['LOW']['p95'],
                min_sla=min(p[c]['sla_hit'] for c in CLS), offchain=1 - gl['onchain_units_per_tx'], done_ratio=gl['completed_to_arrived_ratio'],
                backlog_p95=gl['backlog_p95'], switches=res.get('switches', np.nan), low_starv=starv(res, SIM))
DEV_RHOS = [0.5, 0.7, 0.85, 0.95]; NS = int(os.environ.get('NSEEDS', 20))
def run_one(args):
    name, rho, sd = args; pol, P = VAR[name]
    arr = ns['make_arrivals'](W, rho, 5000 + sd, SIM)
    res = ns['simulate6'](arr, W, pol, rho, SIM, P); rows, gl = ns['summarize'](res, SIM)
    return dict(variant=name, rho=rho, seed=sd, **metrics_of(res, rows, gl))
def periodic(nb, period, offset, length):
    m = np.zeros(nb, bool)
    for s in range(offset, nb, period): m[s:s+length] = True
    return m
def run_dip(args):
    name, rho, sd, c = args; pol, P = VAR[name]
    arr = ns['make_arrivals'](W, rho, 7000 + sd, SIM); nb = len(W['dt'])
    dip = periodic(nb, 1008, 500, 72); cm = np.where(dip, c, 1.0)
    res = ns['simulate6'](arr, W, pol, rho, SIM, P, cap_mult=cm); rows, gl = ns['summarize'](res, SIM)
    # recovery: blocks after each dip end until backlog <= 1 capacity (limit 500)
    ends = [i + 1 for i in range(nb - 1) if dip[i] and not dip[i + 1]]; rec = []
    for e in ends:
        seg = res['backlog'][e:e + 500] / SIM['CAP']; ok = np.where(seg <= 1.0)[0]; rec.append(ok[0] if len(ok) else 500)
    blk = np.searchsorted(arr['t_end'], res['arr_t'], side='right').clip(0, nb - 1)
    inwin = np.zeros(nb, bool)
    for e in ends: inwin[max(0, e - 72):min(nb, e + 72)] = True
    m = inwin[blk]; lat = res['lat'][m]; cl = res['cls'][m]
    p95 = [np.percentile(lat[cl == k], 95) if (cl == k).sum() else np.nan for k in range(3)]
    return dict(variant=name, rho=rho, seed=sd, cap=c, win_macro_p95=np.nanmean(p95), recovery=np.mean(rec), offchain=1 - gl['onchain_units_per_tx'], **{k: v for k, v in metrics_of(res, rows, gl).items() if k in ('min_sla','low_starv','switches','macro_p95')})
if __name__ == '__main__':
    stage = sys.argv[1]
    names = list(VAR)
    if stage == 'dev':
        jobs = [(n, r, s) for n in names for r in DEV_RHOS for s in range(NS)]; t0 = time.time()
        with Pool(2) as p: R = p.map(run_one, jobs, chunksize=8)
        pd.DataFrame(R).to_csv(S0 + '/dev6_results.csv', index=False); print('dev done', len(jobs), 'runs', round(time.time() - t0), 's')
    if stage == 'dip':
        jobs = [(n, r, s, c) for n in names for r in [0.5, 0.7] for s in range(8) for c in [0.6, 0.4]]; t0 = time.time()
        with Pool(2) as p: R = p.map(run_dip, jobs, chunksize=4)
        pd.DataFrame(R).to_csv(S0 + '/dip6_results.csv', index=False); print('dip done', len(jobs), round(time.time() - t0), 's')
    pickle.dump(dict(VAR=VAR, Ls=Ls), open(S0 + '/var6.pkl', 'wb'))
