"""EXP-BALANCE-001c — retention (eta), retro-audit (k), survival floor (b0).

Frozen 001 core (iter 2) + 001b local network/seeding. Exactly three new
knobs (PREREG_001c). Arm A: eta x k, no reinvest. Arm B: b0 survival floor,
reinvest. Single run, no calibration. Prediction fixed in prereg §3.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    idx = np.arange(N_USERS)
    cols = [np.roll(idx, s) for s in (-4, -3, -2, -1, 1, 2, 3, 4)]
    extra = rng.integers(0, N_USERS, N_USERS)
    extra = np.where(extra == idx, (extra + 1) % N_USERS, extra)
    return np.stack(cols + [extra], axis=1)


def run(stickiness, trust_lr, seed, T, seed_frac=0.05,
        eta=0.0, k_audit=0, b0=None, reinvest=False):
    rng = np.random.default_rng(seed)
    q = rng.uniform(0.35, 0.75, M_SELLERS)
    q_hist_mean = q.mean()  # for retro-audit sampling of "own past buys"
    alloc = rng.dirichlet([1.5, 3.0, 1.5], M_SELLERS)
    profit_ema = np.zeros(M_SELLERS)
    rev_ema = np.ones(M_SELLERS)
    q_hat = np.full(M_SELLERS, 0.5)
    cur = np.zeros(N_USERS, dtype=int)
    tau = np.stack([np.full(N_USERS, 0.60), np.full(N_USERS, 0.40)], axis=1)
    neigh = build_neighbors(rng)
    is_seed = np.zeros(N_USERS, dtype=bool)
    if seed_frac > 0:
        sid = rng.choice(N_USERS, int(N_USERS * seed_frac), replace=False)
        cur[sid] = 1
        tau[sid, 1] = 0.60
        is_seed[sid] = True
    rows = np.arange(N_USERS)
    share_trace = np.empty(T)
    qbar_trace = np.empty(T)
    wbribe_trace = np.empty(T)
    alive_trace = np.empty(T)
    prev_cur = cur.copy()
    for t in range(T):
        if reinvest:
            norm = rev_ema / (rev_ema.mean() + 1e-9)
            budget = b0 + (1 - b0) * norm
        else:
            budget = np.ones(M_SELLERS)
        bribe = alloc[:, 1] * budget
        ads = alloc[:, 2] * budget
        recon = rng.random(N_USERS) < RECONSIDER
        d = BETA * (tau[:, 1] - tau[:, 0])
        # eta: value-retention lowers leaving prob for seeded cohort
        leave_bias = eta * is_seed
        p_to_hon = 1.0 / (1.0 + np.exp(-(d - C_SWITCH - stickiness)))
        p_to_inc = 1.0 / (1.0 + np.exp(-(-d - C_SWITCH - leave_bias)))  # sign fixed vs 001c
        u = rng.random(N_USERS)
        go_hon = recon & (cur == 0) & (u < p_to_hon)
        go_inc = recon & (cur == 1) & (u < p_to_inc)
        cur[go_hon] = 1
        cur[go_inc] = 0
        # retro-audit: on arrival to honest, k virtual updates from own history
        if k_audit > 0:
            arrived = go_hon
            if arrived.any():
                na = int(arrived.sum())
                virt = q_hist_mean + rng.normal(0, SIGMA_OUT, (na, k_audit))
                for j in range(k_audit):
                    tau[arrived, 1] = np.clip(
                        tau[arrived, 1] + trust_lr * (virt[:, j] - tau[arrived, 1]),
                        0, 1)
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
        if len(idx_inc):
            ex = idx_inc[rng.random(len(idx_inc)) < EPS_EXPLORE]
            if len(ex):
                buy[ex] = rng.choice(M_SELLERS, len(ex), p=p_hon)
                rec_index[ex] = 1
        ads_tot = ads.sum()
        if ads_tot > 1e-9:
            p_ad = ADS_PROB_MAX * ads_tot / (ads_tot + M_SELLERS * 0.33)
            ad_u = rng.random(N_USERS) < p_ad
            if ad_u.any():
                buy[ad_u] = rng.choice(M_SELLERS, int(ad_u.sum()), p=ads / ads_tot)
                rec_index[ad_u] = -1
        s = q[buy] + rng.normal(0, SIGMA_OUT, N_USERS)
        for k2 in (0, 1):
            m = rec_index == k2
            if m.any():
                tau[m, k2] = np.clip(tau[m, k2] + trust_lr * (s[m] - tau[m, k2]), 0, 1)
        partners = neigh[rows, rng.integers(0, 9, N_USERS)]
        k_sp = cur[partners]
        tau[rows, k_sp] += WOM * (tau[partners, k_sp] - tau[rows, k_sp])
        panel = cur == 1
        if panel.any():
            sums = np.bincount(buy[panel], weights=s[panel], minlength=M_SELLERS)
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
        q_hist_mean = 0.98 * q_hist_mean + 0.02 * q[buy].mean()
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
        alive_trace[t] = (q > 0.2).sum()
    return dict(share=share_trace, qbar=qbar_trace,
                wbribe=wbribe_trace, alive=alive_trace,
                seed_ret=float(cur[is_seed].mean()) if is_seed.any() else None)


def e_hold(share, thr=0.55, need=200):
    ok = share >= thr
    run_len = 0
    for i, v in enumerate(ok):
        run_len = run_len + 1 if v else 0
        if run_len >= need:
            return i - need + 1
    return None


def main():
    res = {"armA": {}, "armB": {}}
    # ---- Arm A: eta x k ----
    print("=== ARM A (eta x k) ===")
    gridA = {}
    for eta in [0.0, 0.5, 1.0, 2.0]:
        for k in [0, 10, 30]:
            tr = [run(1.0, 0.04, s, T=1600, seed_frac=0.05, eta=eta, k_audit=k)
                  for s in SEEDS]
            share = np.mean([r["share"] for r in tr], axis=0)
            holds = [e_hold(r["share"]) for r in tr]
            gridA[f"{eta}_{k}"] = dict(
                final=float(share[-1]),
                ehold=[h if h is not None else "no" for h in holds],
                seed_ret=float(np.mean([r["seed_ret"] for r in tr])),
                traj=share[::8].tolist())
            print(f"eta={eta} k={k}: final={share[-1]:.3f} "
                  f"ehold={gridA[f'{eta}_{k}']['ehold']} "
                  f"seed_ret={gridA[f'{eta}_{k}']['seed_ret']:.2f}")
    res["armA"] = gridA
    # ---- Arm B: survival floor ----
    print("=== ARM B (b0 survival floor) ===")
    gridB = {}
    for b0 in [0.0, 0.5]:
        for st in [0.0, 1.0]:
            tr = [run(st, 0.08, s, T=800, seed_frac=0.05, eta=1.0,
                      k_audit=10, b0=b0, reinvest=True) for s in SEEDS]
            share = np.mean([r["share"] for r in tr], axis=0)
            gridB[f"{b0}_{st}"] = dict(
                final=float(share[-1]),
                qbar_T=float(np.mean([r["qbar"][-1] for r in tr])),
                alive_T=float(np.mean([r["alive"][-1] for r in tr])),
                wbribe_T=float(np.mean([r["wbribe"][-1] for r in tr])),
                alive_traj=np.mean([r["alive"] for r in tr], 0)[::4].tolist(),
                share_traj=share[::4].tolist())
            g = gridB[f"{b0}_{st}"]
            print(f"b0={b0} st={st}: share={g['final']:.3f} qbar={g['qbar_T']:.3f} "
                  f"alive={g['alive_T']:.1f}/24 w_bribe={g['wbribe_T']:.3f}")
    res["armB"] = gridB
    json.dump(res, open("results_001c_fix.json", "w"), indent=1)

    # ---- figures ----
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
    for k, mk in [(0, "o-"), (10, "s-"), (30, "^-")]:
        etas = [0.0, 0.5, 1.0, 2.0]
        ax[0].plot(etas, [gridA[f"{e}_{k}"]["final"] for e in etas], mk,
                   label=f"k={k}")
    ax[0].axhline(0.55, color="r", ls=":", lw=1, label="порог E_hold")
    ax[0].axhline(0.30, color="gray", ls=":", lw=1, label="стационар 001b")
    ax[0].set_title("Арм A: финальная доля vs η")
    ax[0].set_xlabel("η (удержание)"); ax[0].legend(fontsize=8)
    for key, lab in [("0.0_0", "η0 k0"), ("2.0_0", "η2 k0"),
                     ("0.0_30", "η0 k30"), ("2.0_30", "η2 k30")]:
        tt = np.arange(len(gridA[key]["traj"])) * 8
        ax[1].plot(tt, gridA[key]["traj"], label=lab)
    ax[1].axhline(0.55, color="r", ls=":", lw=1)
    ax[1].set_title("Арм A: траектории (углы сетки)")
    ax[1].set_xlabel("тик"); ax[1].legend(fontsize=8)
    for key, lab in [("0.0_1.0", "b0=0"), ("0.5_1.0", "b0=0.5")]:
        tt = np.arange(len(gridB[key]["alive_traj"])) * 4
        ax[2].plot(tt, gridB[key]["alive_traj"], label=lab)
    ax[2].set_title("Арм B: живые продавцы (q>0.2), stickiness=1")
    ax[2].set_xlabel("тик"); ax[2].set_ylabel("из 24"); ax[2].legend()
    fig.tight_layout()
    fig.savefig("fig_001c_fix.png", dpi=150)
    print("done")


if __name__ == "__main__":
    main()
