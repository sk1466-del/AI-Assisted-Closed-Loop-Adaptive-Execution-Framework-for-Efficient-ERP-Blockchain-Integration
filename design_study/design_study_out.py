import pandas as pd, numpy as np
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S0='/tmp/claude-0/-home-claude/a2dcfc82-0cf4-5fb0-ac72-9f9115551e02/scratchpad/dev6'
d=pd.read_csv(S0+'/dev6_results.csv'); dp=pd.read_csv(S0+'/dip6_results.csv')
ns=d.seed.nunique()
def paired(a,b,metric,pct):
    r=[]
    for s in range(ns):
        x=d[(d.seed==s)&(d.variant==a)][metric].mean(); y=d[(d.seed==s)&(d.variant==b)][metric].mean()
        r.append(100*(x-y)/y if pct else x-y)
    r=np.array(r); return r.mean(), stats.t.ppf(.975,len(r)-1)*r.std(ddof=1)/np.sqrt(len(r))
NAMES={'BEST_FIXED':'BEST_FIXED (CONG)','ADAPTIVE_v5':'ADAPTIVE (frozen v5.2.1 grid)','ADAPT_fine':'ADAPTIVE, fine grid','CONST_fine':'  no forecast (constant load), fine grid',
 'FEEDBACK_fine':'FEEDBACK (backlog only), fine grid','ADAPT_fine_hyst':'  + hysteresis','ADAPT_fine_dwell':'  + recovery hold','ADAPT_fine_hyst_dwell':'  + hysteresis + recovery hold',
 'ADAPT_q80':'  + uncertainty-aware (q80) forecast','ADAPT_meanx':'  control: mean forecast × 1.15','ADAPT_fine_guard':'  + fairness guard','MPC':'MPC (fluid model)'}
rows=[]
for k,nm in NAMES.items():
    sub=d[d.variant==k]; r=dict(Controller=nm.strip(), indent=nm.startswith(' '))
    r['Off-chain share']=sub.offchain.mean()
    if k!='BEST_FIXED':
        a,ha=paired(k,'BEST_FIXED','macro_p95',True); b,hb=paired(k,'BEST_FIXED','offchain',False)
        r['Off-chain saving vs BEST_FIXED']=-b; r['Latency cost % vs BEST_FIXED']=a; r['lat_ci']=ha
        r['Saving per 1 % latency']=(-b)/a if a>0 else np.nan
    else: r['Off-chain saving vs BEST_FIXED']=0.0; r['Latency cost % vs BEST_FIXED']=0.0; r['lat_ci']=0.0; r['Saving per 1 % latency']=np.nan
    r['Regime switches (13,175 blocks)']=sub.switches.mean()
    r['Min class SLA']=sub.min_sla.mean(); r['LOW starvation %']=100*sub.low_starv.mean()
    s6=dp[(dp.variant==k)&(dp.cap==0.6)]; s4=dp[(dp.variant==k)&(dp.cap==0.4)]
    r['Recovery blocks (dip to 60 %)']=s6.recovery.mean(); r['Recovery blocks (dip to 40 %)']=s4.recovery.mean()
    rows.append(r)
T=pd.DataFrame(rows); T.to_csv('/home/claude/figs/table_design_study_validation.csv',index=False)
pd.set_option('display.width',250); print(T.drop(columns=['indent']).round(3).to_string())
# figure
Ok=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9','#F0E442','#666666']
fig,ax=plt.subplots(figsize=(7.2,4.6),dpi=200)
sty={'ADAPTIVE_v5':('o','#D55E00'),'ADAPT_fine':('o','#D55E00'),'CONST_fine':('s','#009E73'),'FEEDBACK_fine':('^','#0072B2'),'ADAPT_fine_hyst':('D','#E69F00'),'ADAPT_fine_dwell':('D','#E69F00'),
 'ADAPT_fine_hyst_dwell':('D','#E69F00'),'ADAPT_q80':('v','#CC79A7'),'ADAPT_meanx':('v','#CC79A7'),'ADAPT_fine_guard':('x','#D55E00'),'MPC':('P','#666666')}
lab={'ADAPTIVE_v5':'ADAPTIVE (v5.2.1 grid)','ADAPT_fine':'ADAPTIVE (fine grid)','CONST_fine':'no forecast','FEEDBACK_fine':'backlog only','ADAPT_fine_hyst':'+ hysteresis','ADAPT_fine_dwell':'+ recovery hold','ADAPT_fine_hyst_dwell':'+ both','ADAPT_q80':'+ q80 forecast','ADAPT_meanx':'mean × 1.15','MPC':'MPC (fluid)'}
OFF={'ADAPTIVE_v5':(10,-12),'ADAPT_fine':(-48,-22),'CONST_fine':(34,-20),'FEEDBACK_fine':(-10,14),'ADAPT_fine_hyst':(-40,22),'ADAPT_fine_dwell':(-30,-24),'ADAPT_fine_hyst_dwell':(-58,-4),'ADAPT_q80':(40,-18),'ADAPT_meanx':(30,22),'MPC':(-10,16)}
HA={k:'left' for k in OFF}
for _,r in T.iterrows():
    k=[kk for kk,v in NAMES.items() if v.strip()==r.Controller][0]
    if k in ('BEST_FIXED','ADAPT_fine_guard'): continue
    m,c=sty[k]; ax.errorbar(r['Latency cost % vs BEST_FIXED'],r['Off-chain saving vs BEST_FIXED'],xerr=r['lat_ci'],fmt=m,color=c,ms=7,mfc=c if k!='ADAPT_fine_hyst_dwell' else 'none',capsize=2,lw=1)
    ax.annotate(lab[k],(r['Latency cost % vs BEST_FIXED'],r['Off-chain saving vs BEST_FIXED']),xytext=OFF[k],textcoords='offset points',fontsize=7.5,ha=HA[k],arrowprops=dict(arrowstyle='-',color='#999',lw=.5))
ax.axhline(0,color='#999',lw=.8); ax.set_xlabel('Latency cost relative to BEST_FIXED, class-averaged p95 (%)   (mean of 4 loads, 20 seeds, validation period)',fontsize=8.5)
ax.set_ylabel('Off-chain share saved vs BEST_FIXED (absolute)',fontsize=8.5); ax.set_xlim(0,7); ax.set_ylim(-0.01,0.24)
for s in ('top','right'): ax.spines[s].set_visible(False)
ax.grid(alpha=.25); ax.tick_params(labelsize=8); ax.set_title('Added mechanisms slide along one trade-off line; backlog-only and MPC fall below it',fontsize=9.5)
fig.tight_layout(); fig.savefig('/home/claude/figs/fig_design_study.png'); fig.savefig('/home/claude/figs/fig_design_study.pdf')
