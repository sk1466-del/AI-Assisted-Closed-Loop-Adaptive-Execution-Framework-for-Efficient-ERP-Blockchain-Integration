# =====================================================================================================
# EXPERIMENT A (validation period ONLY): does the demand forecast help once regime changes take effect k blocks late?
# Paste this as ONE new cell at the END of the v5.2.1 notebook (after the tuning cell has run, i.e. after TUNED/L_star exist).
# It does not modify any existing variable or result.  Nothing here touches the held-out test period.
#
# Pre-specified question and decision rule (written BEFORE seeing results):
#   Delay model : a regime chosen at the start of block j is applied at block j+k (k = 0, 2, 5, 10); before that the previous
#                 decision stays in force.  (Fabric-like batch timeout / anchoring setup time.)  k = 0 is the main-paper setting.
#   Policies    : BEST_FIXED (CONG), FEEDBACK (backlog only), ADAPTIVE_CONST (backlog + average load), ADAPTIVE (backlog + forecast).
#   Tuning      : per k, on validation, same grid/budget/eps-rule as the paper (3 loads, 1 seed).
#   Evaluation  : 20 fresh validation seeds (5000+), loads 0.5/0.7/0.85/0.95, identical arrivals for all policies, paired 95% CIs.
#   "Forecast helps at k" iff  (saving_ADAPTIVE - saving_ADAPTIVE_CONST) has a 95% CI above 0  AND
#                              (latency_ADAPTIVE - latency_ADAPTIVE_CONST) <= +0.5 percentage points.
# =====================================================================================================
import numpy as np, pandas as pd, time, itertools, scipy.stats as st

K_LIST   = [0, 2, 5, 10]                 # actuation delays (blocks) to test
N_EVAL   = 20                            # evaluation seeds (reduce to 10 for a quicker first look)
EVAL_RHO = [0.5, 0.7, 0.85, 0.95]
GRID_LO_ = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8]; GRID_HI_ = [0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0, 2.5]   # fine grid, same for every policy
# (a coarse grid makes ADAPTIVE_CONST degenerate: it then sits in CONG all the time and saves nothing, which would flatter the forecast)
POLS     = ["FEEDBACK", "ADAPTIVE_CONST", "ADAPTIVE"]

def simulate_delay(arr, world, policy, rho, S, P, k):
    nb = len(world["dt"]); offs = arr["offs"]
    q_t, q_c, q_s, q_o = np.empty(0), np.empty(0, int), np.empty(0), np.empty(0, bool)
    L, C, A, CT, used, backlog, counts, decided = [], [], [], [], np.zeros(nb), np.zeros(nb), {}, []
    for j in range(nb):
        decided.append(decide(policy, j, len(q_t) / S["CAP"], arr, world, rho, S, P))      # decision made now ...
        rname = decided[j - k] if j >= k else "CONG"                                          # ... takes effect k blocks later
        counts[rname] = counts.get(rname, 0) + 1
        s, e = offs[j], offs[j + 1]
        if e > s:
            q_t = np.concatenate([q_t, arr["t"][s:e]]); q_c = np.concatenate([q_c, arr["cls"][s:e]])
            q_s = np.concatenate([q_s, arr["size"][s:e]]); q_o = np.concatenate([q_o, arr["off"][s:e]])
        t = arr["t_end"][j]; mask, u = select_block(t, q_t, q_c, q_s, q_o, REG[rname], S)
        if mask.any():
            L.append(t - q_t[mask]); C.append(q_c[mask]); A.append(q_t[mask]); CT.append(np.full(int(mask.sum()), t)); keep = ~mask
            q_t, q_c, q_s, q_o = q_t[keep], q_c[keep], q_s[keep], q_o[keep]
        used[j] = u; backlog[j] = len(q_t)
    cat = lambda l, d: np.concatenate(l) if l else np.empty(0, d)
    return dict(lat=cat(L, float), cls=cat(C, int), arr_t=cat(A, float), comp_t=cat(CT, float), arrivals_t=arr["t"], arrivals_cls=arr["cls"], used=used, backlog=backlog, q_t=q_t, q_c=q_c,
                t_end=arr["t_end"][-1], t_warm=arr["t_end"][int(S["WARMUP_FRAC"] * nb)], j_warm=int(S["WARMUP_FRAC"] * nb), n_arrived=len(arr["t"]), reg=counts)

def run_one(arr, pol, rho, P, k):
    res = simulate_delay(arr, W_D, pol, rho, SIM, P, k); rows, g = summarize(res, SIM)
    p = {r["cls"]: r for r in rows}
    macro = float(np.mean([p[c]["p95"] for c in CLS]))
    return dict(obj=objective_from_rows(rows), macro=macro, off=1 - g["onchain_units_per_tx"], sla_min=min(p[c]["sla_hit"] for c in CLS))

# ---- world on the validation period (forecast = the paper's selected model; training-only demand scale) ----
dem_val_pred_D = TB["fitted"][TB["SEL"]].predict(df[FEATURES_DEM].iloc[SL["va"]])
W_D = make_world(SL["va"], {"ADAPTIVE": dem_val_pred_D})

# ---- sanity: k = 0 must reproduce the paper's simulator exactly ----
_a = make_arrivals(W_D, 0.7, 4242, SIM); _P = {"ADAPTIVE": (0.4, 0.6, "I"), "FEEDBACK": (0.4, 0.6), "ADAPTIVE_CONST": (0.4, 0.6, "I"), "BEST_FIXED": "CONG"}
for _pol in POLS:
    _r0 = simulate(_a, W_D, _pol, 0.7, SIM, _P); _r1 = simulate_delay(_a, W_D, _pol, 0.7, SIM, _P, 0)
    assert np.array_equal(_r0["lat"], _r1["lat"]) and np.array_equal(_r0["backlog"], _r1["backlog"]), f"k=0 mismatch for {_pol}"
print("sanity OK: k=0 reproduces the paper's simulator for", POLS)

ARR_T = {(rho, i): make_arrivals(W_D, rho, 1000 + 17 * i, SIM) for i, rho in enumerate(TUNE_RHOS)}        # tuning arrivals (1 seed)
ARR_E = {(rho, s): make_arrivals(W_D, rho, 5000 + 31 * s + int(rho * 100), SIM) for rho in EVAL_RHO for s in range(N_EVAL)}   # evaluation arrivals

def tune_k(k):
    def ev(pol, P):
        r = [run_one(a, pol, rho, P, k) for (rho, _), a in ARR_T.items()]
        return float(np.mean([x["obj"] for x in r])), float(np.mean([x["off"] for x in r]))
    pairs = [(lo, hi) for lo in GRID_LO_ for hi in GRID_HI_ if hi > lo]; cands = []
    o, f = ev("BEST_FIXED", {"BEST_FIXED": "CONG"}); cands.append(dict(key="BEST_FIXED", params="CONG", obj=o, offload=f))
    for g in pairs:
        o, f = ev("FEEDBACK", {"FEEDBACK": g}); cands.append(dict(key="FEEDBACK", params=g, obj=o, offload=f))
    for pol in ["ADAPTIVE_CONST", "ADAPTIVE"]:
        for mode in ["I"]:
            for g in pairs:
                p3 = (g[0], g[1], mode); o, f = ev(pol, {pol: p3}); cands.append(dict(key=pol, params=p3, obj=o, offload=f))
    Ls = min(c["obj"] for c in cands); T = {}
    for key in ["BEST_FIXED"] + POLS:
        pool = [c for c in cands if c["key"] == key]; ok = [c for c in pool if c["obj"] <= (1 + EPS_TOL) * Ls]
        T[key] = (min(ok, key=lambda c: c["offload"]) if ok else min(pool, key=lambda c: c["obj"]))["params"]
    return T

def ci(x):
    x = np.asarray(x, float); n = len(x); h = st.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n); return x.mean(), h

rows_out, t0 = [], time.time()
for k in K_LIST:
    T = tune_k(k); print(f"\n--- k={k}: tuned ({time.time()-t0:.0f}s) ->", T, flush=True)
    P = dict(BEST_FIXED="CONG", FEEDBACK=T["FEEDBACK"], ADAPTIVE_CONST=T["ADAPTIVE_CONST"], ADAPTIVE=T["ADAPTIVE"])
    per = {pol: {s: [] for s in range(N_EVAL)} for pol in ["BEST_FIXED"] + POLS}
    for (rho, s), a in ARR_E.items():
        for pol in ["BEST_FIXED"] + POLS:
            per[pol][s].append(run_one(a, pol, rho, P, k))
    M = {pol: {m: np.array([np.mean([r[m] for r in per[pol][s]]) for s in range(N_EVAL)]) for m in ("macro", "off", "sla_min")} for pol in per}
    for pol in POLS:
        sav = M["BEST_FIXED"]["off"] - M[pol]["off"]; lat = 100 * (M[pol]["macro"] / M["BEST_FIXED"]["macro"] - 1)
        rows_out.append(dict(k=k, policy=pol, params=str(T[pol]), saving=sav.mean(), saving_ci=ci(sav)[1], latency_cost_pct=lat.mean(), latency_ci=ci(lat)[1], min_sla=M[pol]["sla_min"].mean()))
    sa, sc_, sf = (M["BEST_FIXED"]["off"] - M[p]["off"] for p in ("ADAPTIVE", "ADAPTIVE_CONST", "FEEDBACK"))
    la, lc, lf = (100 * (M[p]["macro"] / M["BEST_FIXED"]["macro"] - 1) for p in ("ADAPTIVE", "ADAPTIVE_CONST", "FEEDBACK"))
    d_s, h_s = ci(sa - sc_); d_l, h_l = ci(la - lc)
    helps = (d_s - h_s > 0) and (d_l <= 0.5)
    if sc_.mean() < 0.02: print("   WARNING: ADAPTIVE_CONST saves almost nothing here (degenerate comparison); do not read the verdict below.")
    print(f"k={k:2d}  ADAPTIVE - CONST : saving {d_s:+.4f} ± {h_s:.4f}   latency {d_l:+.2f} ± {h_l:.2f} pp   => forecast helps? {helps}")
    ds2, hs2 = ci(sa - sf); dl2, hl2 = ci(la - lf)
    print(f"        ADAPTIVE - FEEDBACK: saving {ds2:+.4f} ± {hs2:.4f}   latency {dl2:+.2f} ± {hl2:.2f} pp")
    rows_out.append(dict(k=k, policy="DIFF ADAPTIVE-CONST", saving=d_s, saving_ci=h_s, latency_cost_pct=d_l, latency_ci=h_l, params=f"forecast_helps={helps}"))
    rows_out.append(dict(k=k, policy="DIFF ADAPTIVE-FEEDBACK", saving=ds2, saving_ci=hs2, latency_cost_pct=dl2, latency_ci=hl2, params=""))
R = pd.DataFrame(rows_out); R.to_csv("table_actuation_delay_validation.csv", index=False)
print("\n", R.round(4).to_string(index=False)); print(f"\nTotal time {time.time()-t0:.0f}s.  Saved table_actuation_delay_validation.csv  (send me this CSV)")
