import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({"font.family":"DejaVu Sans","savefig.dpi":300})
def box(ax,x,y,w,h,title,body,col,dashed=False,fs=8.6):
    p=FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.01,rounding_size=0.012",fc="white",ec=col,lw=1.8,ls=(0,(4,3)) if dashed else "-");ax.add_patch(p)
    ax.text(x+w/2,y+h-0.022,title,ha="center",va="top",fontsize=fs+0.6,fontweight="bold",color="#111")
    ax.text(x+w/2,y+h-0.062,body,ha="center",va="top",fontsize=fs,color="#333",linespacing=1.25)
def layer(ax,y,h,col,num,name,fc):
    ax.add_patch(FancyBboxPatch((0.01,y),0.955,h,boxstyle="round,pad=0.005,rounding_size=0.015",fc=fc,ec=col,lw=2.2))
    ax.add_patch(plt.Circle((0.04,y+h-0.027),0.017,fc=col,ec="none")); ax.text(0.04,y+h-0.027,str(num),ha="center",va="center",color="white",fontsize=9,fontweight="bold")
    ax.text(0.068,y+h-0.027,name,va="center",fontsize=11,fontweight="bold",color=col)
def arrow(ax,y0,y1,label):
    ax.annotate("",xy=(0.5,y1),xytext=(0.5,y0),arrowprops=dict(arrowstyle="-|>",lw=2,color="#222"))
    ax.text(0.52,(y0+y1)/2,label,fontsize=8.6,style="italic",va="center",color="#222")
# ---------------- Fig 1
fig=plt.figure(figsize=(9,10.2)); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,1.02); ax.set_ylim(0,1); ax.axis("off")
B,G,P,O="#2358A6","#1E8A4C","#7A3E9D","#D9822B"
layer(ax,0.775,0.205,B,1,"Enterprise data layer","#EAF0FA")
for i,(t,b) in enumerate([("Block process","Real inter-block\nintervals (trace)"),("Demand","Transactions per block,\nsize, weight"),("Features","Lagged counts, rolling\nmeans, burst flag,\nqueue-pressure index"),("ERP workload (assumed)","Classes 10/60/30 %,\nsizes, off-loadable\nshare, SLA 3,600 s")]):
    box(ax,0.02+i*0.2375,0.787,0.222,0.125,t,b,B)
arrow(ax,0.772,0.732,"backlog and lagged features")
layer(ax,0.525,0.205,G,2,"Optimisation engine","#EAF5EE")
box(ax,0.02,0.537,0.30,0.135,"Demand forecaster","Gradient boosting, selected on\nvalidation (next-6-block demand)\nrelative to training mean",G)
box(ax,0.34,0.537,0.30,0.135,"Backlog-driven controller","s = backlog (+ forecast load)\ns ≤ lo: PRIO   lo < s < hi: MID\ns ≥ hi: CONG   (lo=0.4, hi=0.6)",G)
box(ax,0.66,0.537,0.30,0.135,"ε-constraint tuning","Validation period only; least\noff-chain use within 5 % of the\nbest latency objective",G)
arrow(ax,0.522,0.482,"execution regime")
layer(ax,0.275,0.205,P,3,"Blockchain execution layer (simulated)","#F3ECF8")
box(ax,0.02,0.287,0.222,0.135,"Priority ordering","Class weight + aging\n(1,800 s)",P)
box(ax,0.2575,0.287,0.222,0.135,"Off-chain batching","Batches of 10 / 25,\none anchor per batch",P)
box(ax,0.495,0.287,0.222,0.135,"Block service","Capacity 100 units\nper block (real timing)",P)
box(ax,0.7325,0.287,0.235,0.135,"Consensus, Merkle proofs,\nIPFS, Fabric (design only)","PBFT / Raft / PoS; not\nmodelled or evaluated",P,dashed=True,fs=8)
arrow(ax,0.272,0.232,"latency, backlog, off-chain share")
layer(ax,0.025,0.205,O,4,"Performance feedback layer","#FDF1E5")
box(ax,0.02,0.037,0.30,0.135,"Monitoring","p95 per class, SLA attainment,\nstarvation, completed TPS",O)
box(ax,0.34,0.037,0.30,0.135,"Drift detection","Page–Hinkley on forecast error\n(chunks of 144 blocks)",O)
box(ax,0.66,0.037,0.30,0.135,"Recalibration","Retrain forecaster on the last\n6,000 blocks (cooldown 2 chunks)",O)
ax.annotate("",xy=(0.985,0.60),xytext=(0.985,0.10),arrowprops=dict(arrowstyle="-|>",lw=1.8,color=O,connectionstyle="arc3,rad=0"))
ax.text(0.9,0.003,"solid = implemented and evaluated;  dashed = design only",ha="right",fontsize=8.5,color="#444")
ax.text(0.9915,0.35,"updated forecaster",rotation=90,fontsize=8.2,color=O,ha="left",va="center")
fig.savefig("/home/claude/figs/fig1_framework.png",bbox_inches="tight"); fig.savefig("/home/claude/figs/fig1_framework.pdf",bbox_inches="tight"); plt.close(fig)
# ---------------- Fig 2
fig=plt.figure(figsize=(11,4.6)); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
steps=[("1  Data","66,532 real Bitcoin blocks\n2020-01 to 2021-03\n(public block APIs)",B),("2  Split","Train 2020-01..09\nValidation 2020-10..12\nHeld-out test 2021-01..03\n6-block embargo",B),
("3  Forecast","Features after block i−1\nTask A: interval (control)\nTask B: next-6-block demand\nselect on validation",G),("4  Simulate","Poisson arrivals scaled by\nreal demand to load ρ;\nidentical across policies;\nreal block times",P),
("5  Policies","STATIC, PRIO_ONLY,\nBEST_FIXED, FEEDBACK,\nADAPTIVE + ablations,\nORACLE",P),("6  Evaluate","5 seeds, paired 95 % CIs,\nmatched off-chain share,\nstress tests, sensitivity,\nthree-way verdicts",O)]
w=0.14; gap=0.022
for i,(t,b,c) in enumerate(steps):
    x=0.025+i*(w+gap); box(ax,x,0.42,w,0.30,t,b,c,fs=8.4)
    if i<5: ax.annotate("",xy=(x+w+gap-0.002,0.57),xytext=(x+w+0.002,0.57),arrowprops=dict(arrowstyle="-|>",lw=1.8,color="#222"))
ax.annotate("",xy=(0.025+2*(w+gap)+w/2,0.41),xytext=(0.025+5*(w+gap)+w/2,0.41),arrowprops=dict(arrowstyle="-|>",lw=1.6,color=O,connectionstyle="arc3,rad=-0.35",ls="--"))
ax.text(0.5,0.12,"closed loop: Page–Hinkley drift detection and recalibration of the forecaster (tuning of thresholds on validation only)",ha="center",fontsize=8.8,style="italic",color=O)
ax.text(0.5,0.93,"Evaluation workflow (design frozen as code version v5.2.1, hash d6c30b92b47d5336)",ha="center",fontsize=11,fontweight="bold")
fig.savefig("/home/claude/figs/fig2_workflow.png",bbox_inches="tight"); fig.savefig("/home/claude/figs/fig2_workflow.pdf",bbox_inches="tight"); plt.close(fig)
