import build5, patch52
CELLS = [list(x) for x in patch52.apply(build5.CELLS)]
def sub(i, old, new):
    assert old in CELLS[i][1], "missing: " + old[:60]
    CELLS[i][1] = CELLS[i][1].replace(old, new, 1)
# data-source unification: public Esplora APIs are the default; BigQuery is optional/lazy
sub(1, "!pip -q install pyarrow requests google-cloud-bigquery db-dtypes", "!pip -q install pyarrow requests")
sub(3, "    from google.cloud import bigquery\n", "    import subprocess, sys; subprocess.run([sys.executable, '-m', 'pip', '-q', 'install', 'google-cloud-bigquery', 'db-dtypes'])\n    from google.cloud import bigquery\n")
sub(4, "observation_unit=\"one Bitcoin block\",",
    "observation_unit=\"one Bitcoin block\", data_source=DATA_SOURCE, "
    "data_source_detail=(\"public Esplora-compatible block APIs (mempool.space primary, blockstream.info fallback)\" if DATA_SOURCE == \"api\" else \"Google BigQuery bigquery-public-data.crypto_bitcoin.blocks\"), "
    "block_height_min=int(raw[\"number\"].min()), block_height_max=int(raw[\"number\"].max()), duplicate_heights=int(raw[\"number\"].duplicated().sum()),")

# ---- v5.2.1: leak-free demand normalisation, versioned hash, renamed ratio, completed-TPS in sensitivity ----
sub(2, "CONFIG_HASH = hashlib.sha256(json.dumps(dict(", "CODE_VERSION = \"v5.2.1\"   # bump on ANY change that can alter results\nNORMALISATION = \"demand scale = TRAINING-period mean (fixed reference for validation and confirmation)\"\nCONFIG_HASH = hashlib.sha256(json.dumps(dict(CODE_VERSION=CODE_VERSION, NORMALISATION=NORMALISATION,")
sub(2, 'print("DESIGN FREEZE hash:", CONFIG_HASH,', 'print("CODE VERSION:", CODE_VERSION, "|", NORMALISATION)\nprint("DESIGN FREEZE hash:", CONFIG_HASH,')
sub(4, 'SIM["DT_MEAN"] = float(df[TARGET_INT].iloc[:a_tr].mean())',
    'SIM["DT_MEAN"] = float(df[TARGET_INT].iloc[:a_tr].mean())\n'
    'DEMAND_SCALE = float(df[TARGET_DEM].iloc[:a_tr].mean())   # TRAINING-only reference for normalising demand/forecasts (no val/test statistic enters the controller)')
sub(4, "observation_unit=\"one Bitcoin block\",", "observation_unit=\"one Bitcoin block\", code_version=CODE_VERSION, demand_scale_train_mean=DEMAND_SCALE,")
sub(9, "dem = df[TARGET_DEM].iloc[sl].values.astype(float); sc = dem.mean()",
       "dem = df[TARGET_DEM].iloc[sl].values.astype(float); sc = DEMAND_SCALE   # fixed TRAINING mean: no information from the evaluated period")
for i in range(len(CELLS)):
    if CELLS[i][0] == "code" and "completion_ratio" in CELLS[i][1]:
        CELLS[i][1] = CELLS[i][1].replace("completion_ratio", "completed_to_arrived_ratio")
# per-class completed TPS in the printed/saved results
sub(12, '"completed_tps", "arrival_tps", "completed_to_arrived_ratio",', '"completed_tps", "completed_tps_HIGH", "completed_tps_NORMAL", "completed_tps_LOW", "arrival_tps", "completed_to_arrived_ratio",')
sub(12, '    print("-- throughput / footprint / backlog / unfinished / regime usage --"); display(gl.round(3))',
    '    print("-- COMPLETED throughput (tx confirmed per second in the window) / footprint / backlog / unfinished / regime usage --"); display(gl.round(4))')
sub(12, "sim_df = pd.DataFrame(all_rows); sim_df.to_csv(", "sim_df = pd.DataFrame(all_rows)\n_tp = [\"completed_tps\", \"completed_tps_HIGH\", \"completed_tps_NORMAL\", \"completed_tps_LOW\", \"arrival_tps\", \"completed_to_arrived_ratio\"]\nsim_df[sim_df.cls == \"ALL\"].query(\"seg == 0\").groupby([\"rho\", \"policy\"])[_tp].agg([\"mean\", \"std\"]).to_csv(f\"{OUT_DIR}/table_completed_tps.csv\")\nsim_df.to_csv(")
# sensitivity (main cell 15): completed TPS added
sub(15, "acc[pol].append((np.mean([r[\"p95\"] for r in rws if r[\"cls\"] in CLS]), 1 - g_[\"onchain_units_per_tx\"]))",
        "acc[pol].append((np.mean([r[\"p95\"] for r in rws if r[\"cls\"] in CLS]), 1 - g_[\"onchain_units_per_tx\"], g_[\"completed_tps\"]))")
sub(15, "    mp = {p: np.mean([a[0] for a in v]) for p, v in acc.items()}; of = {p: np.mean([a[1] for a in v]) for p, v in acc.items()}",
        "    mp = {p: np.mean([a[0] for a in v]) for p, v in acc.items()}; of = {p: np.mean([a[1] for a in v]) for p, v in acc.items()}; ct = {p: np.mean([a[2] for a in v]) for p, v in acc.items()}")
sub(15, "                     ADAPT_vs_CONST_macro_p95_pct=", "                     completed_tps_BEST_FIXED=ct[\"BEST_FIXED\"], completed_tps_ADAPTIVE=ct[\"ADAPTIVE\"], completed_tps_change_pct=100 * (ct[\"ADAPTIVE\"] - ct[\"BEST_FIXED\"]) / ct[\"BEST_FIXED\"],\n                     ADAPT_vs_CONST_macro_p95_pct=")
for c_ in CELLS:
    if c_[0] == "code": c_[1] = c_[1].replace("/content/results_v5", "/content/results_v5_2_1")   # never mix with the old v5 outputs
for c_ in CELLS:
    c_[1] = c_[1].replace("| **Confirmation test** | **2021-01-01 → 2021-03-31** | **never used during design. Run it ONCE. Do not change anything afterwards** |",
                          "| **Held-out test** | **2021-01-01 → 2021-03-31** | **chronologically after all tuning, but re-used across design iterations (v1–v5.2.1) - it is NOT an independent confirmation set** |")
# WORDING-4: 2021-Q1 is a held-out chronological test period re-used across design iterations, NOT an independent confirmation (labels only; nothing inside the design hash changes)
for c_ in CELLS:
    for a_, b_ in [("CONFIRMATION TEST period:", "HELD-OUT TEST period (re-used across design iterations; NOT an independent confirmation):"), ("REAL confirmation period (2021-Q1)", "REAL held-out test period (2021-Q1)"),
                   ("confirmation period", "held-out test period"), ("confirmation test 2021-01..03 (untouched)", "held-out test 2021-01..03 (re-used across design iterations; not independent)"), ("confirmation test", "held-out test")]:
        c_[1] = c_[1].replace(a_, b_)
CELLS = [tuple(x) for x in CELLS]
