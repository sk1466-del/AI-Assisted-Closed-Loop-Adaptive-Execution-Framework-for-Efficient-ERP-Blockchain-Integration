import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
S='/tmp/claude-0/-home-claude/a2dcfc82-0cf4-5fb0-ac72-9f9115551e02/scratchpad/rstress2/'
O='/home/claude/figs/'
plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.alpha":.25,"figure.dpi":150,"savefig.dpi":300,"axes.titlesize":10,"legend.frameon":False})
COL={"STATIC":"#666666","PRIO_ONLY":"#E69F00","BEST_FIXED":"#0072B2","FEEDBACK":"#009E73","ADAPTIVE":"#D55E00","ORACLE":"#000000","ADAPTIVE_CONST":"#CC79A7","ADAPTIVE_SHUFFLED":"#56B4E9","ADAPTIVE_FROZEN":"#999900"}
MK={"BEST_FIXED":"s","FEEDBACK":"^","ADAPTIVE":"o","ORACLE":"D","ADAPTIVE_CONST":"v","ADAPTIVE_SHUFFLED":"P","ADAPTIVE_FROZEN":"X","STATIC":"x","PRIO_ONLY":"+"}
def ci(x):
    x=np.asarray(x,float); n=len(x)
    return stats.t.ppf(.975,n-1)*x.std(ddof=1)/np.sqrt(n) if n>1 else 0
def save(fig,name): fig.savefig(O+name+".png",bbox_inches="tight"); fig.savefig(O+name+".pdf",bbox_inches="tight"); plt.close(fig)

# ---- Pareto: mean +- 95% CI over 5 seeds
d=pd.read_csv(S+'sim_raw_results.csv'); d=d[d.seg==0]
a=d[d.cls=="ALL"].set_index(["rho","seed","policy"]); a["off"]=1-a["onchain_units_per_tx"]
m=d[d.cls.isin(["HIGH","NORMAL","LOW"])].groupby(["rho","seed","policy"])["p95"].mean().rename("macro")
t=a[["off"]].join(m).reset_index()
pols=["BEST_FIXED","FEEDBACK","ADAPTIVE","ADAPTIVE_CONST","ADAPTIVE_SHUFFLED","ADAPTIVE_FROZEN","ORACLE"]
fig,axs=plt.subplots(1,4,figsize=(13,3.4))
for ax,rho in zip(axs,[0.5,0.7,0.85,0.95]):
    for p in pols:
        x=t[(t.rho==rho)&(t.policy==p)]
        big=p=="ADAPTIVE"
        ax.errorbar(x.off.mean(),x.macro.mean(),xerr=ci(x.off),yerr=ci(x.macro),fmt=MK[p],color=COL[p],ms=11 if big else 6,mfc="none" if big else COL[p],mew=1.8 if big else 1,capsize=2,label=p.replace("ADAPTIVE","ADAPT"),alpha=.95,zorder=5 if big else 3)
    ax.set_title(f"offered load ρ = {rho}"); ax.set_xlabel("off-chain share of payload"); ax.set_ylabel("macro p95 latency (s)")
h,l=axs[0].get_legend_handles_labels(); fig.legend(h,l,loc="lower center",ncol=7,bbox_to_anchor=(.5,-.08))
fig.suptitle("Latency vs on-chain retention (mean ± 95% CI, 5 seeds; lower-left is better; hollow circle = ADAPT, overlaps others when identical; STATIC/PRIO_ONLY off-scale)",y=1.02,fontsize=10)
fig.tight_layout(); save(fig,"fig_pareto")

# ---- Fairness: LOW starvation + LOW p95 vs load
f=pd.read_csv(S+'table_fairness.csv')
fp=["STATIC","PRIO_ONLY","BEST_FIXED","FEEDBACK","ADAPTIVE"]
fig,axs=plt.subplots(1,3,figsize=(12,3.4))
for p in fp:
    x=f[f.policy==p]; ls="--" if p=="ADAPTIVE" else "-"
    axs[0].plot(x.rho,x.LOW_starvation*100,ls,marker=MK[p] if p!="STATIC" else "o",color=COL[p],label=p)
    axs[1].plot(x.rho,x.LOW_p95,ls,marker="o",color=COL[p],label=p)
    axs[2].plot(x.rho,x.HIGH_p95,ls,marker="o",color=COL[p],label=p)
axs[0].set_ylabel("LOW starvation rate (% of tx, wait > 3×SLA)"); axs[0].set_title("(a) Starvation of LOW class")
axs[1].set_yscale("log"); axs[1].set_ylabel("LOW p95 latency (s, log)"); axs[1].set_title("(b) LOW-class p95")
axs[2].set_yscale("log"); axs[2].set_ylabel("HIGH p95 latency (s, log)"); axs[2].set_title("(c) HIGH-class p95")
for ax in axs: ax.set_xlabel("offered load ρ"); ax.set_xticks([0.5,0.7,0.85,0.95])
axs[1].axhline(3600,color="gray",ls=":"); axs[1].text(.86,2900,"SLA 3,600 s",color="gray",fontsize=8)
axs[0].legend(); fig.tight_layout(); save(fig,"fig_fairness")

# ---- Capacity dip: recovery + macro p95
c=pd.read_csv(S+'table_capacity_dip.csv'); cp=["STATIC","BEST_FIXED","FEEDBACK","ADAPTIVE_CONST","ADAPTIVE"]
fig,axs=plt.subplots(1,2,figsize=(10,3.4),sharey=False)
for ax,col,tt,yl in [(axs[0],"recovery_blocks","(a) Blocks to drain the backlog after the dip","blocks to recover (log; plotted as blocks + 1)"),(axs[1],"window_macro_p95","(b) Macro p95 inside the dip window","s")]:
    for rho,off in [(0.5,-.2),(0.7,.2)]:pass
    xs=np.arange(3); w=.16
    for i,p in enumerate(cp):
        v=[c[(c.policy==p)&(c.capacity_during_dip==cd)][col].mean() for cd in [0.4,0.6,0.8]]
        ax.bar(xs+(i-2)*w,np.array(v)+(1 if col=="recovery_blocks" else 0),w,color=COL[p],label=p.replace("ADAPTIVE","ADAPT"))
    ax.set_xticks(xs); ax.set_xticklabels(["40 %","60 %","80 %"]); ax.set_xlabel("capacity during the dip"); ax.set_title(tt); ax.set_ylabel(yl)
    if col=="recovery_blocks": ax.set_yscale("log")
axs[0].legend(loc="upper right"); fig.suptitle("Temporary capacity dip (mean of ρ = 0.5 and 0.7, 5 seeds; assumed shape, not measured)",y=1.03,fontsize=10)
fig.tight_layout(); save(fig,"fig_capacity_dip")

# ---- Bursty
b=pd.read_csv(S+'table_bursty.csv'); bp=["STATIC","BEST_FIXED","FEEDBACK","ADAPTIVE_CONST","ADAPTIVE"]
sc=list(b.scenario.unique()); short=["S1 sudden\n(unannounced)","S2 month-end\n(announced)","S3 month-end\n(unannounced)"]
fig,axs=plt.subplots(1,2,figsize=(11,3.4))
for ax,col,tt,yl in [(axs[0],"window_macro_p95","(a) Macro p95 inside the burst window","s"),(axs[1],"offchain_share","(b) Off-chain share","share")]:
    xs=np.arange(3); w=.16
    for i,p in enumerate(bp):
        v=[b[(b.policy==p)&(b.scenario==s)][col].mean() for s in sc]
        ax.bar(xs+(i-2)*w,v,w,color=COL[p],label=p.replace("ADAPTIVE","ADAPT"))
    ax.set_xticks(xs); ax.set_xticklabels(short); ax.set_title(tt); ax.set_ylabel(yl)
fig.legend(*axs[0].get_legend_handles_labels(),loc="lower center",ncol=5,bbox_to_anchor=(.5,-.1)); fig.suptitle("Bursty ERP scenarios (mean of base ρ = 0.3 and 0.6, 5 seeds; assumed shapes)",y=1.03,fontsize=10)
fig.tight_layout(); save(fig,"fig_bursty")

# ---- Segments
sg=d.copy()
