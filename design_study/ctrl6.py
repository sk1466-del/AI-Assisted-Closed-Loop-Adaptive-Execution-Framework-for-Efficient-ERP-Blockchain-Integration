# ---- v6 controllers (hysteresis + recovery + fairness guard + uncertainty-aware forecast) and an MPC competitor ----
LVL = ["PRIO", "MID", "CONG"]
def mu_of(rname, S):
    reg = REG[rname]; share = sum(S["CLASS_P"][c] for c in reg["elig"]) * S["OFFLOADABLE_P"]
    return 1.0 / ((1 - share) + share / reg["B"])          # service capacity in units of fully on-chain block capacity
def make_world6(sl, rel_maps):
    dt = df[TARGET_INT].iloc[sl].values.astype(float); dem = df[TARGET_DEM].iloc[sl].values.astype(float); sc = DEMAND_SCALE
    rh = {k: np.clip(np.asarray(v) / sc, 0.2, 3.0) for k, v in rel_maps.items()}
    return dict(dt=dt, rel=dem / sc, rel_hat=rh)
def u_hat_of(world, uq, j, rho, S):
    if uq == 'none': return 0.0
    return rho * world["rel_hat"][uq][j] * S["DT_MEAN"] / 600.0
def stat_s(br0, u, mode, S):
    return br0 + u if mode == "I" else max(0.0, br0 + S["H"] * (u - 1.0))
def decide_hr(st, s, oldest_wait, P, S):
    lo, hi, dl, dw, g = P["lo"], P["hi"], P["delta"], P["dwell"], P.get("guard")
    r = st["r"]
    up = 2 if s >= hi else (1 if s >= lo else 0)
    if r == 2: dn = 2 if s > hi - dl else (1 if s > lo - dl else 0)
    elif r == 1: dn = 1 if s > lo - dl else 0
    else: dn = 0
    cand = max(up, dn)
    if cand < r and st["since"] < dw: cand = r
    if g is not None and oldest_wait > g * S["SLA"]: cand = 2
    st["since"] = 0 if cand != r else st["since"] + 1
    st["r"] = cand
    return LVL[cand]
def decide_mpc(br0, u, P, S):
    for r in LVL:                                    # lightest off-chain use first
        b = max(0.0, br0 + P["H"] * (u - MU[r]))      # fluid backlog after H blocks under regime r, constant forecast load
        if b <= P["bmax"]: return r
    return "CONG"
MU = {r: mu_of(r, SIM) for r in LVL}
def simulate6(arr, world, policy, rho, S, P, cap_mult=None):
    nb = len(world["dt"]); offs = arr["offs"]
    q_t, q_c, q_s, q_o = np.empty(0), np.empty(0, int), np.empty(0), np.empty(0, bool)
    L, C, A, CT, used, backlog, counts = [], [], [], [], np.zeros(nb), np.zeros(nb), {}
    st = {"r": 0, "since": 0}; nsw = 0; prev = None; guard_hits = 0
    for j in range(nb):
        br0 = len(q_t) / S["CAP"]
        if policy in ("HR", "MPC"):
            u = u_hat_of(world, P["uq"], j, rho, S)
            if policy == "HR":
                ow = (arr["t_end"][j] - world["dt"][j] - q_t.min()) if len(q_t) else 0.0
                rname = decide_hr(st, stat_s(br0, u, P["mode"], S), ow, P, S)
            else: rname = decide_mpc(br0, u, P, S)
        else: rname = decide(policy, j, br0, arr, world, rho, S, P)
        counts[rname] = counts.get(rname, 0) + 1
        if prev is not None and rname != prev: nsw += 1
        prev = rname
        s, e = offs[j], offs[j + 1]
        if e > s:
            q_t = np.concatenate([q_t, arr["t"][s:e]]); q_c = np.concatenate([q_c, arr["cls"][s:e]])
            q_s = np.concatenate([q_s, arr["size"][s:e]]); q_o = np.concatenate([q_o, arr["off"][s:e]])
        t = arr["t_end"][j]
        Sj = S if cap_mult is None else dict(S, CAP=S["CAP"] * cap_mult[j])
        mask, u_ = select_block(t, q_t, q_c, q_s, q_o, REG[rname], Sj)
        if mask.any():
            L.append(t - q_t[mask]); C.append(q_c[mask]); A.append(q_t[mask]); CT.append(np.full(int(mask.sum()), t)); keep = ~mask
            q_t, q_c, q_s, q_o = q_t[keep], q_c[keep], q_s[keep], q_o[keep]
        used[j] = u_; backlog[j] = len(q_t)
    cat = lambda l, d: np.concatenate(l) if l else np.empty(0, d)
    return dict(lat=cat(L, float), cls=cat(C, int), arr_t=cat(A, float), comp_t=cat(CT, float), arrivals_t=arr["t"], arrivals_cls=arr["cls"], used=used, backlog=backlog, q_t=q_t, q_c=q_c,
                t_end=arr["t_end"][-1], t_warm=arr["t_end"][int(S["WARMUP_FRAC"] * nb)], j_warm=int(S["WARMUP_FRAC"] * nb),
                n_arrived=len(arr["t"]), reg=counts, switches=nsw)
