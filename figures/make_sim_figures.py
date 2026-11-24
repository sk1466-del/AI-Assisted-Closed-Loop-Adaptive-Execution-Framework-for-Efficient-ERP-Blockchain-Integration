import pickle, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
exec(open('make_csv_figures.py').read().split("# ---- Pareto")[0])
K=pickle.load(open('/tmp/claude-0/-home-claude/a2dcfc82-0cf4-5fb0-ac72-9f9115551e02/scratchpad/figrun/keep.pkl','rb'))
SLA=3600
sty={"STATIC":("-",1.6),"BEST_FIXED":("-",3.6),"FEEDBACK":("-",1.4),"ADAPTIVE":((0,(3,2)),1.6)}
alpha={"BEST_FIXED":.55}
# CDF
fig,axs=plt.subplots(1,3,figsize=(12.5,3.5),sharey=True)
for ax,(cn,ci_) in zip(axs,[("HIGH",0),("NORMAL",1),("LOW",2)]):
    for p in ["STATIC","BEST_FIXED","FEEDBACK","ADAPTIVE"]:
        r=K[p]; m=(r["arr_t"]>=r["t_warm"])&(r["cls"]==ci_); x=np.sort(r["lat"][m])
        ls,lw=sty[p]; ax.plot(x,np.arange(1,len(x)+1)/len(x),ls=ls,lw=lw,color=COL[p],alpha=alpha.get(p,1),label=p,zorder=4 if p=="ADAPTIVE" else 3)
    ax.set_xscale("log"); ax.set_xlim(10,1.2e5); ax.set_title(f"{cn} priority"); ax.set_xlabel("latency (s, log scale)")
    ax.axvline(SLA,color="gray",ls=":"); ax.text(SLA*1.08,0.04,"SLA",color="gray",fontsize=8)
axs[0].set_ylabel("CDF of confirmed tx"); axs[0].legend(loc="upper left")
fig.suptitle("Latency CDF by class (ρ = 0.85, seed 0). BEST_FIXED and ADAPTIVE overlap almost exactly",y=1.02,fontsize=10)
fig.tight_layout(); save(fig,"fig_latency_cdf_by_class")
# Backlog
fig,ax=plt.subplots(figsize=(10,3.6))
for p in ["STATIC","BEST_FIXED","FEEDBACK","ADAPTIVE"]:
    y=pd.Series(K[p]["backlog"]).rolling(144).mean().values; ls,lw=sty[p]
    ax.plot(y,ls=ls,lw=lw,color=COL[p],alpha=alpha.get(p,1),label=p,zorder=4 if p=="ADAPTIVE" else 3)
ax.set_yscale("symlog",linthresh=10); ax.set_ylim(0,6000)
ax.set_xlabel("block index (test period)"); ax.set_ylabel("backlog (tx, 144-block mean, symlog)")
ax.set_title("Backlog over time (ρ = 0.85, seed 0): hybrid policies stay near zero, STATIC accumulates"); ax.legend(ncol=4,loc="upper left")
fig.tight_layout(); save(fig,"fig_backlog")
