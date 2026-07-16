"""EXP-BALANCE-001b — time, seeding, flywheel.

Frozen 001 core (calibration iteration 2). Exactly three pre-registered
manipulations (PREREG_EXP-BALANCE-001b.md):
  Q1 horizon T=3200;  Q2 local WOM network + seeded cohorts;
  Q3 revenue-funded budgets (two-sided flywheel).
No calibration permitted. Single run. Everything publishes.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- frozen structural constants (001, iteration 2) ----------
N_USERS = 1200
M_SELLERS = 24
SEEDS = [11, 22, 33]
BETA = 6.0
C_SWITCH = 1.50
WOM = 0.02
EPS_EXPLORE = 0.02
RECONSIDER = 0.20
SIGMA_OUT = 0.25
Q_GROW = 0.010
Q_DEP = 0.004
MARGIN = 0.40
IMIT_EVERY = 20
IMIT_COPY = 0.8
TEMP = 0.10
W_BRIBE_RANK = 0.7
W_Q_RANK = 0.3
Q_NOISE_INC = 0.15
QHAT_PRIOR_N = 20.0
ADS_PROB_MAX = 0.15


def softmax(x, temp=TEMP):
    z = (x - x.max()) / temp
    e = np.exp(z)
    return e / e.sum()


def build_neighbors(rng):
    """Ring k=8 (+-1..4) plus one random long link per user -> (N, 9)."""
    idx = np.arange(N_USERS)
    cols = [np.roll(idx, s) for s in (-4, -3, -2, -1, 1, 2, 3, 4)]
    extra = rng.integers(0, N_USERS, N_USERS)
    extra = np.where(extra == idx, (extra + 1) % N_USERS, extra)
    return np.stack(cols + [extra], axis=1)


def run(stickiness, trust_lr, seed, T, topology="global",
        seed_frac=0.0, seed_mode="scatter", reinvest=False,
        honest_present=True):
    rng = np.random.default_rng(seed)
    q = rng.uniform(0.35, 0.75, M_SELLERS)
    alloc = rng.dirichlet([1.5, 3.0, 1.5], M_SELLERS)
    profit_ema = np.zeros(M_SELLERS)
    rev_ema = np.ones(M_SELLERS)
    q_hat = np.full(M_SELLERS, 0.5)
    cur = np.zeros(N_USERS, dtype=int)
    tau = np.stack([np.full(N_USERS, 0.60), np.full(N_USERS, 0.40)], axis=1)
    neigh = build_neighbors(rng) if topology == "local" else None
    seed_ids = np.array([], dtype=int)
    if seed_frac > 0:
        k = int(N_USERS * seed_frac)
        seed_ids = (np.arange(k) if seed_mode == "cluster"
                    else rng.choice(N_USERS, k, replace=False))
        cur[seed_ids] = 1
        tau[seed_ids, 1] = 0.60   # equal to population's prior in incumbent
    rows = np.arange(N_USERS)
    share_trace = np.empty(T)
    qbar_trace = np.empty(T)
    wbribe_trace = np.empty(T)
    for t in range(T):
        budget = rev_ema if reinvest else np.ones(M_SELLERS)
        bribe = alloc[:, 1] * budget
        ads = alloc[:, 2] * budget
        if honest_present:
            recon = rng.random(N_USERS) < RECONSIDER
            d = BETA * (tau[:, 1] - tau[:, 0])
            p_to_hon = 1.0 / (1.0 + np.exp(-(d - C_SWITCH - stickiness)))
            p_to_inc = 1.0 / (1.0 + np.exp(-(-d - C_SWITCH)))
            u = rng.random(N_USERS)
            go_hon = recon & (cur == 0) & (u < p_to_hon)
            go_inc = recon & (cur == 1) & (u < p_to_inc)
            cur[go_hon] = 1
            cur[go_inc] = 0
        inc_score = (W_BRIBE_RANK * bribe / (bribe.mean() + 1e-9)
                     + W_Q_RANK * (q + rng.normal(0, Q_NOISE_INC, M_SELLERS)))
        p_inc = softmax(inc_score)
        p_hon = softmax(q_hat)
        buy = np.empty(N_USERS, dtype=int)
        idx_inc = np.where(cur == 0)[0]
        idx_hon = np.where(cur == 1)[0]
        if len(idx_inc):
            buy[idx_inc] = rng.choice(M_SELLERS, len(idx_inc), p=p_inc)
        if len(idx_hon):
            buy[idx_hon] = rng.choice(M_SELLERS, len(idx_hon), p=p_hon)
        rec_index = cur.copy()
        if honest_present and len(idx_inc):
            ex = idx_inc[rng.random(len(idx_inc)) < EPS_EXPLORE]
            if len(ex):
                buy[ex] = rng.choice(M_SELLERS, len(ex), p=p_hon)
                rec_index[ex] = 1
        ads_tot = ads.sum()
        if ads_tot > 1e-9:
            p_ad = ADS_PROB_MAX * ads_tot / (ads_tot + M_SELLERS * 0.33)
            ad_u = rng.random(N_USERS) < p_ad
            if ad_u.any():
                buy[ad_u] = rng.choice(M_SELLERS, int(ad_u.sum()),
                                       p=ads / ads_tot)
                rec_index[ad_u] = -1
        s = q[buy] + rng.normal(0, SIGMA_OUT, N_USERS)
        for k2 in (0, 1):
            m = rec_index == k2
            if m.any():
                tau[m, k2] = np.clip(
                    tau[m, k2] + trust_lr * (s[m] - tau[m, k2]), 0, 1)
        if honest_present:
            partners = (neigh[rows, rng.integers(0, 9, N_USERS)]
                        if topology == "local"
                        else rng.integers(0, N_USERS, N_USERS))
            k_sp = cur[partners]
            tau[rows, k_sp] += WOM * (tau[partners, k_sp] - tau[rows, k_sp])
            panel = cur == 1
            if panel.any():
                sums = np.bincount(buy[panel], weights=s[panel],
                                   minlength=M_SELLERS)
                cnts = np.bincount(buy[panel], minlength=M_SELLERS)
                nz = cnts > 0
                mean_s = np.zeros(M_SELLERS)
                mean_s[nz] = sums[nz] / cnts[nz]
                w = cnts / (cnts + QHAT_PRIOR_N)
                q_hat = (1 - w) * q_hat + w * mean_s
        sales = np.bincount(buy, minlength=M_SELLERS)
        rev = sales / (N_USERS / M_SELLERS)
        rev_ema = 0.9 * rev_ema + 0.1 * rev
        fitness = rev if reinvest else sales * MARGIN / (N_USERS / M_SELLERS) - 1.0
        profit_ema = 0.95 * profit_ema + 0.05 * fitness
        q = np.clip(q + Q_GROW * alloc[:, 0] * budget * (1 - q) - Q_DEP * q, 0, 1)
        if (t + 1) % IMIT_EVERY == 0:
            peer = rng.integers(0, M_SELLERS, M_SELLERS)
            better = profit_ema[peer] > profit_ema
            new_alloc = alloc.copy()
            new_alloc[better] = (IMIT_COPY * alloc[peer[better]]
                                 + (1 - IMIT_COPY) * alloc[better])
            noise = rng.dirichlet([30, 30, 30], M_SELLERS)
            new_alloc = 0.9 * new_alloc + 0.1 * noise
            alloc = new_alloc / new_alloc.sum(1, keepdims=True)
        share_trace[t] = (cur == 1).mean()
        qbar_trace[t] = q.mean()
        wbribe_trace[t] = alloc[:, 1].mean()
    out = dict(share=share_trace, qbar=qbar_trace, wbribe=wbribe_trace)
    if len(seed_ids):
        out["seed_retention"] = float(cur[seed_ids].mean())
        if topology == "local":
            nb = np.unique(neigh[seed_ids].ravel())
            nb = nb[~np.isin(nb, seed_ids)]
            out["neigh_share"] = float(cur[nb].mean())
    return out


def tau50(share, win=50):
    roll = np.convolve(share, np.ones(win) / win, mode="valid")
    hits = np.where(roll >= 0.5)[0]
    return int(hits[0] + win) if len(hits) else None


def main():
    res = {}
    # ---------- Q1: time ----------
    q1 = {}
    for st in [0.0, 0.5, 1.0]:
        tr = [run(st, 0.04, s, T=3200) for s in SEEDS]
        shares = np.mean([r["share"] for r in tr], axis=0)
        t50s = [tau50(r["share"]) for r in tr]
        q1[st] = dict(final=float(shares[-1]),
                      t50=[t if t is not None else "none" for t in t50s],
                      traj=shares[::8].tolist())
        print(f"Q1 stickiness={st}: final={shares[-1]:.3f}, tau50={q1[st]['t50']}")
    res["Q1"] = q1
    # ---------- Q2: seeding ----------
    q2 = {}
    for mode in ["cluster", "scatter"]:
        for sf in [0.0, 0.02, 0.05, 0.10]:
            key = f"local_{mode}_{sf}"
            tr = [run(1.0, 0.04, s, T=1600, topology="local",
                      seed_frac=sf, seed_mode=mode) for s in SEEDS]
            fin = float(np.mean([r["share"][-1] for r in tr]))
            ret = (float(np.mean([r.get("seed_retention", np.nan) for r in tr]))
                   if sf > 0 else None)
            nbs = (float(np.mean([r.get("neigh_share", np.nan) for r in tr]))
                   if sf > 0 else None)
            t50s = [tau50(r["share"]) for r in tr]
            q2[key] = dict(final=fin, retention=ret, neigh=nbs,
                           t50=[t if t is not None else "none" for t in t50s],
                           traj=np.mean([r["share"] for r in tr], 0)[::8].tolist())
            print(f"Q2 {key}: final={fin:.3f} retention={ret} neigh={nbs} "
                  f"tau50={q2[key]['t50']}")
    for sf in [0.0, 0.05]:
        key = f"global_scatter_{sf}"
        tr = [run(1.0, 0.04, s, T=1600, seed_frac=sf) for s in SEEDS]
        q2[key] = dict(final=float(np.mean([r["share"][-1] for r in tr])))
        print(f"Q2 {key}: final={q2[key]['final']:.3f}")
    res["Q2"] = q2
    # ---------- Q3: flywheel ----------
    q3 = {}
    cf = [run(0, 0.02, s, T=800, reinvest=True, honest_present=False)
          for s in SEEDS]
    cf_q = [float(r["qbar"][-1]) for r in cf]
    cf_wb = np.mean([r["wbribe"] for r in cf], 0)
    print("Q3 counterfactual (reinvest) qbar_T:", [round(x, 4) for x in cf_q])
    for st in [0.0, 1.0, 2.0]:
        for lr in [0.02, 0.08]:
            tr = [run(st, lr, s, T=800, reinvest=True) for s in SEEDS]
            fin = float(np.mean([r["share"][-1] for r in tr]))
            dq = float(np.mean([r["qbar"][-1] - cf_q[i]
                                for i, r in enumerate(tr)]))
            wb_T = float(np.mean([r["wbribe"][-1] for r in tr]))
            q3[f"{st}_{lr}"] = dict(
                final=fin, dq=dq, wbribe_T=wb_T,
                wbribe_traj=np.mean([r["wbribe"] for r in tr], 0)[::4].tolist(),
                qbar_traj=np.mean([r["qbar"] for r in tr], 0)[::4].tolist())
            print(f"Q3 st={st} lr={lr}: share={fin:.3f} dq={dq:+.4f} "
                  f"w_bribe_T={wb_T:.3f}")
    q3["cf_wbribe_traj"] = cf_wb[::4].tolist()
    q3["cf_qbar_traj"] = np.mean([r["qbar"] for r in cf], 0)[::4].tolist()
    res["Q3"] = q3
    json.dump(res, open("results_001b.json", "w"), indent=1)

    # ---------- figures ----------
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
    for st in [0.0, 0.5, 1.0]:
        tt = np.arange(len(q1[st]["traj"])) * 8
        ax[0].plot(tt, q1[st]["traj"], label=f"stickiness={st}")
    ax[0].axhline(0.5, color="k", ls=":", lw=1)
    ax[0].set_title("Q1: доля честного, T=3200 (lr=0.04)")
    ax[0].set_xlabel("тик"); ax[0].legend()
    sfs = [0.0, 0.02, 0.05, 0.10]
    for mode, mk in [("cluster", "o-"), ("scatter", "s--")]:
        ax[1].plot(sfs, [q2[f"local_{mode}_{sf}"]["final"] for sf in sfs],
                   mk, label=f"локальная сеть, {mode}")
    ax[1].plot([0.0, 0.05],
               [q2["global_scatter_0.0"]["final"],
                q2["global_scatter_0.05"]["final"]],
               "^:", label="глобальное перемешивание")
    ax[1].axhline(0.5, color="k", ls=":", lw=1)
    ax[1].set_title("Q2: финальная доля vs посев (stickiness=1.0)")
    ax[1].set_xlabel("доля посева s"); ax[1].legend(fontsize=8)
    for key, lab in [("0.0_0.08", "st=0, lr=0.08"),
                     ("1.0_0.08", "st=1, lr=0.08"),
                     ("2.0_0.02", "st=2, lr=0.02")]:
        tt = np.arange(len(q3[key]["wbribe_traj"])) * 4
        ax[2].plot(tt, q3[key]["wbribe_traj"], label=lab)
    tt = np.arange(len(q3["cf_wbribe_traj"])) * 4
    ax[2].plot(tt, q3["cf_wbribe_traj"], "k--", label="контрфакт (реинвест)")
    ax[2].set_title("Q3: w_bribe(t) при реинвесте")
    ax[2].set_xlabel("тик"); ax[2].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("fig_001b.png", dpi=150)
    print("done")


if __name__ == "__main__":
    main()
