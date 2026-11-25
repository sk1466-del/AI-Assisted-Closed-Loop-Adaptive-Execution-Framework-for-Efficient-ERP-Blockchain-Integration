import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams['font.family']='DejaVu Sans'
W,H=10.6,13.8
fig=plt.figure(figsize=(W,H)); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis('off')
X0,X1=0.3,9.5
def layer(y,h,col,fill,num,title):
    ax.add_patch(FancyBboxPatch((X0,y),X1-X0,h,boxstyle="round,pad=0,rounding_size=0.18",fc=fill,ec=col,lw=2.2))
    ax.add_patch(plt.Circle((X0+0.42,y+h-0.4),0.22,fc=col,ec='none'))
    ax.text(X0+0.42,y+h-0.4,str(num),color='w',ha='center',va='center',fontsize=12,weight='bold')
    ax.text(X0+0.82,y+h-0.4,title,color=col,ha='left',va='center',fontsize=14,weight='bold')

def row(y,h,col,items,dashed_idx=()):
    n=len(items); gap=0.18; pad=0.25; w=(X1-X0-2*pad-(n-1)*gap)/n
    for i,(t,d) in enumerate(items):
        x=X0+pad+i*(w+gap)
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=0.12",fc='w',ec=col,lw=1.8,ls='--' if i in dashed_idx else '-'))
        ax.text(x+w/2,y+h-0.28,t,ha='center',va='top',fontsize=10.5,weight='bold',wrap=True)
        ax.text(x+w/2,y+h-0.85,d,ha='center',va='top',fontsize=9.2,color='#333',linespacing=1.35)
def arrow(x,y0,y1,label,side='r'):
    ax.add_patch(FancyArrowPatch((x,y0),(x,y1),arrowstyle='-|>',mutation_scale=18,lw=2.2,color='#222'))
    ax.text(x+0.15,(y0+y1)/2,label,fontsize=9.5,style='italic',va='center')
B,G,P,O='#2459a6','#1f8a4c','#7a3f9b','#d9822b'
# layers (top to bottom)
layer(10.9,2.5,B,'#eaf1fa',1,'Enterprise data layer')
row(11.1,1.6,B,[('Block process','Real inter-block\nintervals (trace)'),('Demand','Transactions per\nblock, size, weight'),('Features','Lagged counts, rolling\nmeans, burst flag,\nqueue-pressure index'),('ERP workload\n(assumed)','Classes 10/60/30 %,\nsizes, off-loadable\nshare, SLA 3,600 s')])
arrow(4.9,10.9,10.15,'backlog and lagged features')
layer(7.65,2.5,G,'#eaf5ee',2,'AI-assisted control layer')
row(7.85,1.6,G,[('Demand forecaster','Gradient boosting,\nnext-6-block demand'),('Backlog-driven\ncontroller','s = backlog + forecast load\ns ≤ lo: PRIO, s ≥ hi: CONG,\notherwise MID'),('ε-constraint tuning','Validation period only;\nleast off-chain use within\n5 % of best objective')])
arrow(4.9,7.65,6.9,'execution regime (PRIO / MID / CONG)')
layer(4.4,2.5,P,'#f2eaf7',3,'Blockchain execution layer (simulated)')
row(4.6,1.6,P,[('Priority ordering','Class weight + aging\n(1,800 s)'),('Off-chain batching','Batches of 10 / 25,\none anchor per batch'),('Block service','Capacity 100 units per\nblock (real timing)'),('Consensus, Merkle,\nIPFS, Fabric','Design only; not\nmodelled or evaluated')],dashed_idx=(3,))
arrow(4.9,4.4,3.65,'latency, backlog, off-chain share')
layer(1.15,2.5,O,'#fcf0e4',4,'Performance feedback layer')
row(1.35,1.6,O,[('Monitoring','p95 per class, SLA\nattainment, starvation,\ncompleted TPS'),('Drift detection','Page–Hinkley on forecast\nerror (chunks of 144 blocks)'),('Recalibration','Retrain forecaster on the\nlast 6,000 blocks\n(cooldown 2 chunks)')])
# feedback loop on right
xr=9.95
ax.add_patch(FancyArrowPatch((X1,2.2),(xr,2.2),arrowstyle='-',lw=2.2,color=O))
ax.add_patch(FancyArrowPatch((xr,2.2),(xr,8.5),arrowstyle='-',lw=2.2,color=O))
ax.add_patch(FancyArrowPatch((xr,8.5),(X1,8.5),arrowstyle='-|>',mutation_scale=18,lw=2.2,color=O))
ax.text(xr+0.22,5.3,'updated forecaster (drift-triggered recalibration)',rotation=90,color=O,fontsize=10,ha='center',va='center',style='italic')
ax.text(5.0,0.5,'Solid boxes: implemented and evaluated.  Dashed box: design only.  Orange loop: closed-loop recalibration.',ha='center',fontsize=9.5,color='#444')
fig.savefig('/home/claude/figs/fig1_framework.png',dpi=200); fig.savefig('/home/claude/figs/fig1_framework.pdf')
