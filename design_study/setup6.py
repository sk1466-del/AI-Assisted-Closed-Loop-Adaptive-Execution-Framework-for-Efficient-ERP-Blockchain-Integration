import sys, time, pickle, numpy as np, pandas as pd, builtins, importlib, os, shutil
sys.path.insert(0,'/home/claude/nb6')
CELLS = importlib.import_module('build52').CELLS
S='/tmp/claude-0/-home-claude/a2dcfc82-0cf4-5fb0-ac72-9f9115551e02/scratchpad'
OUT=S+'/dev6'; os.makedirs(OUT,exist_ok=True)
for f in ('api_checkpoint.pkl','blocks_2020-01-01_2021-04-01.parquet'): shutil.copy(f'{S}/rstress2/{f}',OUT)
def display(x): print(x.to_string() if hasattr(x,'to_string') else x)
builtins.display=display
import matplotlib; matplotlib.use("Agg")
done=pickle.load(open(OUT+'/api_checkpoint.pkl','rb'))
rows=[r for v in done.values() for r in v]
r_=pd.DataFrame(rows,columns=["number","ts","transaction_count","size","weight"]).drop_duplicates("number")
r_["block_timestamp"]=pd.to_datetime(r_["ts"],unit="s",utc=True)
r_=r_[(r_.block_timestamp>=pd.Timestamp("2020-01-01",tz="UTC"))&(r_.block_timestamp<pd.Timestamp("2021-04-01",tz="UTC"))]
r_=r_.sort_values("number").reset_index(drop=True)[["number","block_timestamp","transaction_count","size","weight"]]
pd.read_parquet=lambda *a,**k: r_
pd.DataFrame.to_parquet=lambda self,*a,**k: None
ns={"display":display}
codes=[c for t,c in CELLS if t=="code"]
for i in (1,2,3,4,8,9):
    c=codes[i]
    if i==1: c=c.replace('OUT_DIR      = "/content/results_v5_2_1"',f'OUT_DIR = "{OUT}"'); assert OUT in c
    t0=time.time(); print(f"#### CELL {i}",flush=True); exec(compile(c,f"cell{i}","exec"),ns); print(f"-- {time.time()-t0:.0f}s",flush=True)
keys=['df','SL','TB','TA','TARGET_DEM','TARGET_INT','FEATURES_DEM','DEMAND_SCALE','SIM','TUNED','SEED','TUNE_RHOS','TUNE_SEEDS','SLA_FLOOR','EPS_TOL','CLS','H_FWD','tune_df','L_star','CONFIG_HASH','RHOS','GRID_LO','GRID_HI']
pickle.dump({k:ns[k] for k in keys},open(OUT+'/state6.pkl','wb'))
print("STATE SAVED", ns['TUNED'], flush=True)
