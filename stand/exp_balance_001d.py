"""EXP-BALANCE-001d — signal-side network effect (gamma) and bifurcation test.

Frozen 001 core (iter2) + local net/seeding (001b) + retention eta sign-fixed
(001c-fix) + retro-audit k. ONE new knob: gamma scales q_hat prior weight and
category coverage by panel size, closing (or not) the growth loop
share -> accuracy -> inflow -> share. Pre-registered PREREG_001d. Single run.
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
QHAT_PRIOR_N0 = 20.0
ADS_PROB_MAX = 0.15
COV_HALF = 0.15   # panel_frac at which coverage reaches ~1


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


def run(seed, gamma, seed_frac, T=2000, stickiness=1.0, trust_lr=0.04,
        eta=1.0, k_audit=10):
    rng = np.random.default_rng(seed)
    q = rng.uniform(0.35, 0.75, M_SELLERS)
    q_hist_mean = q.mean()
    alloc = rng.dirichlet([1.5, 3.0, 1.5], M_SELLERS)
    profit_ema = np.zeros(M_SELLERS)
    q_hat = np.full(M_SELLERS, 0.5)
    covered = np.zeros(M_SELLERS, dtype=bool)
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
    for t in range(T):
        panel_frac = (cur == 1).mean()
        coverage = min(panel_frac / COV_HALF, 1.0)
        bribe = alloc[:, 1]
        ads = alloc[:, 2]
        recon = rng.random(N_USERS) < RECONSIDER
        d = BETA * (tau[:, 1] - tau[:, 0])
        leave_bias = eta * is_seed
        p_to_hon = 1.0 / (1.0 + np.exp(-(d - C_SWITCH - stickiness)))
        p_to_inc = 1.0 / (1.0 + np.exp(-(-d - C_SWITCH - leave_bias)))
        u = rng.random(N_USERS)
        go_hon = recon & (cur == 0) & (u < p_to_hon)
        go_inc = recon & (cur == 1) & (u < p_to_inc)
        cur[go_hon] = 1
        cur[go_inc] = 0
        if k_audit > 0 and go_hon.any():
            na = int(go_hon.sum())
            virt = q_hist_mean + rng.normal(0, SIGMA_OUT, (na, k_audit))
            for j in range(k_audit):
                tau[go_hon, 1] = np.clip(
                    tau[go_hon, 1] + trust_lr * (virt[:, j] - tau[go_hon, 1]), 0, 1)
        inc_score = (W_BRIBE_RANK * bribe / (bribe.mean() + 1e-9)
                     + W_Q_RANK * (q + rng.normal(0, Q_NOISE_INC, M_SELLERS)))
        p_inc = softmax(inc_score)
        # honest ranks on q_hat but only over covered sellers; uncovered look average
        q_hat_eff = np.where(covered, q_hat, 0.5)
        # coverage gates how sharply honest can prefer covered good sellers
        p_hon = softmax(q_hat_eff * coverage + 0.5 * (1 - coverage))
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
            covered = covered | (cnts >= 3)   # a seller becomes covered once sampled
            mean_s = np.zeros(M_SELLERS)
            mean_s[nz] = sums[nz] / cnts[nz]
            n_eff = QHAT_PRIOR_N0 * (1 + gamma * panel_frac)   # NETWORK EFFECT
            w = cnts / (cnts + n_eff / max(panel_frac * M_SELLERS, 1e-9) * M_SELLERS)
            # simpler, robust: weight by samples vs shrinking prior as panel grows
            w = cnts / (cnts + QHAT_PRIOR_N0 / (1 + gamma * panel_frac))
            q_hat = (1 - w) * q_hat + w * mean_s
        sales = np.bincount(buy, minlength=M_SELLERS)
        profit = sales * MARGIN / (N_USERS / M_SELLERS) - 1.0
        profit_ema = 0.95 * profit_ema + 0.05 * profit
        q = np.clip(q + Q_GROW * alloc[:, 0] * (1 - q) - Q_DEP * q, 0, 1)
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
    return share_trace


def e_hold(share, thr=0.55, need=200):
    ok = share >= thr
    r = 0
    for v in ok:
        r = r + 1 if v else 0
        if r >= need:
            return True
    return False


def main():
    gammas = [0, 1, 3, 8]
    seeds_frac = [0.02, 0.05, 0.10, 0.20]
    grid_final = np.zeros((len(gammas), len(seeds_frac)))
    grid_hold = np.zeros((len(gammas), len(seeds_frac)))
    trajs = {}
    print("=== E1/E2 grid ===")
    for i, g in enumerate(gammas):
        for j, sf in enumerate(seeds_frac):
            tr = [run(s, g, sf) for s in SEEDS]
            share = np.mean(tr, axis=0)
            grid_final[i, j] = share[-1]
            grid_hold[i, j] = np.mean([e_hold(t) for t in tr])
            trajs[f"{g}_{sf}"] = share[::10].tolist()
            print(f"gamma={g} seed={sf}: final={share[-1]:.3f} "
                  f"hold_frac={grid_hold[i,j]:.2f}")
    # E3: bifurcation test at gamma=8, start 5% vs 40%
    print("=== E3 bifurcation (gamma=8) ===")
    lo = [run(s, 8, 0.05) for s in SEEDS]
    hi = [run(s, 8, 0.40) for s in SEEDS]
    lo_f = float(np.mean([t[-1] for t in lo]))
    hi_f = float(np.mean([t[-1] for t in hi]))
    print(f"start 5% -> {lo_f:.3f} | start 40% -> {hi_f:.3f} | gap={hi_f-lo_f:.3f}")
    bif = {"start_5": lo_f, "start_40": hi_f, "gap": hi_f - lo_f,
           "lo_traj": np.mean(lo, 0)[::10].tolist(),
           "hi_traj": np.mean(hi, 0)[::10].tolist()}
    json.dump({"gammas": gammas, "seeds_frac": seeds_frac,
               "final": grid_final.tolist(), "hold": grid_hold.tolist(),
               "trajs": trajs, "bifurcation": bif},
              open("results_001d.json", "w"), indent=1)

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
    im = ax[0].imshow(grid_final, origin="lower", aspect="auto",
                      cmap="viridis", vmin=0, vmax=1)
    ax[0].contour(grid_final, levels=[0.55], colors="w", linewidths=2)
    ax[0].set_xticks(range(len(seeds_frac)), [str(x) for x in seeds_frac])
    ax[0].set_yticks(range(len(gammas)), [str(x) for x in gammas])
    ax[0].set_xlabel("посев s"); ax[0].set_ylabel("γ")
    ax[0].set_title("E1: финальная доля честного")
    fig.colorbar(im, ax=ax[0])
    for g in gammas:
        tt = np.arange(len(trajs[f"{g}_0.1"])) * 10
        ax[1].plot(tt, trajs[f"{g}_0.1"], label=f"γ={g}")
    ax[1].axhline(0.55, color="r", ls=":", lw=1)
    ax[1].set_title("Траектории при посеве 10%")
    ax[1].set_xlabel("тик"); ax[1].legend()
    tt = np.arange(len(bif["lo_traj"])) * 10
    ax[2].plot(tt, bif["lo_traj"], label="старт 5%")
    ax[2].plot(tt, bif["hi_traj"], label="старт 40%")
    ax[2].axhline(0.55, color="r", ls=":", lw=1)
    ax[2].set_title(f"E3: бифуркация γ=8 (разрыв={bif['gap']:.2f})")
    ax[2].set_xlabel("тик"); ax[2].legend()
    fig.tight_layout()
    fig.savefig("fig_001d.png", dpi=150)
    print("done")


if __name__ == "__main__":
    main()
