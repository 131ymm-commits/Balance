"""EXP-BALANCE-001 — headless core of the Balance test stand.

Bought incumbent index (default position, ranks by bribes) vs un-buyable
outcome index; co-evolving sellers allocating budget across
(quality, bribe, disclosed ads). Pre-registered in PREREG_EXP-BALANCE-001.md.
Sweep axes: DEFAULT_STICKINESS x TRUST_LR. Endpoints: E1 honest share,
E2 mean-quality delta vs counterfactual, E3 bribe-allocation trajectory,
E4 incumbent trust-vs-share gap.

CALIBRATION ITERATION 1 (documented; iteration 0 archived as *_iter0):
stand failed its own validity check — the accuracy-wins phase was absent;
switching was noise-dominated (p=0.43 both ways at indifference) and
non-users' belief about the honest index had no formation channel.
Two structural changes, decided BEFORE inspecting E2:
  1) C_SWITCH 0.3 -> 1.5  (indifference inertia)
  2) symmetric word-of-mouth belief diffusion, WOM = 0.02 (both indices)

CALIBRATION ITERATION 2 (final allowed; iteration 1 archived as *_iter1):
symmetric belief AVERAGING erased the minority's earned knowledge —
honest users' tau_hon was dragged toward the uninformed population mean.
One change: word-of-mouth is usage-directed — the listener updates only
the index the speaker currently uses. Experience transmits; averages don't.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- fixed structural constants (pre-registered) ----------
N_USERS = 1200
M_SELLERS = 24
T_TICKS = 400
SEEDS = [11, 22, 33]
BETA = 6.0            # sensitivity of switching to trust difference
C_SWITCH = 1.50       # generic switching cost (indifference inertia; calib 1)
WOM = 0.02            # symmetric word-of-mouth belief diffusion (calib 1)
EPS_EXPLORE = 0.02    # incumbent users sampling honest advice per tick
RECONSIDER = 0.20     # fraction of users reconsidering index per tick
SIGMA_OUT_BASE = 0.25 # outcome noise (robustness slice: 0.15/0.35)
Q_GROW = 0.010
Q_DEP = 0.004
MARGIN = 0.40
IMIT_EVERY = 20
IMIT_COPY = 0.8
TEMP = 0.10           # softmax temperature for both indices
W_BRIBE_RANK = 0.7
W_Q_RANK = 0.3
Q_NOISE_INC = 0.15
QHAT_PRIOR_N = 20.0
ADS_PROB_MAX = 0.15

STICKINESS_AXIS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
TRUST_LR_AXIS = [0.005, 0.01, 0.02, 0.04, 0.08, 0.16]


def softmax(x, temp=TEMP):
    z = (x - x.max()) / temp
    e = np.exp(z)
    return e / e.sum()


def run(stickiness, trust_lr, seed, honest_present=True,
        sigma_out=SIGMA_OUT_BASE, record_traj=False):
    rng = np.random.default_rng(seed)
    q = rng.uniform(0.35, 0.75, M_SELLERS)
    alloc = rng.dirichlet([1.5, 3.0, 1.5], M_SELLERS)  # bribe-skewed start
    profit_ema = np.zeros(M_SELLERS)
    q_hat = np.full(M_SELLERS, 0.5)
    cur = np.zeros(N_USERS, dtype=int)                 # 0 = incumbent, 1 = honest
    tau = np.stack([np.full(N_USERS, 0.60), np.full(N_USERS, 0.40)], axis=1)
    traj = {k: [] for k in ["hon_share", "qbar", "w_bribe",
                            "tau_inc", "share_inc"]}
    for t in range(T_TICKS):
        bribe, ads = alloc[:, 1], alloc[:, 2]
        # --- index switching (behavior; belief is tau) ---
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
        # --- recommendations ---
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
        # --- disclosed ads: consideration outside the rank ---
        ads_tot = ads.sum()
        if ads_tot > 1e-9:
            p_ad = ADS_PROB_MAX * ads_tot / (ads_tot + M_SELLERS * 0.33)
            ad_u = rng.random(N_USERS) < p_ad
            if ad_u.any():
                buy[ad_u] = rng.choice(M_SELLERS, int(ad_u.sum()), p=ads / ads_tot)
                rec_index[ad_u] = -1   # no index advice -> no trust update
        # --- outcomes ---
        s = q[buy] + rng.normal(0, sigma_out, N_USERS)
        for k in (0, 1):
            m = rec_index == k
            if m.any():
                tau[m, k] = np.clip(tau[m, k] + trust_lr * (s[m] - tau[m, k]), 0, 1)
        # word-of-mouth (calib 2): a listener hears about the index the
        # SPEAKER currently uses — experience transmits, averages don't.
        if honest_present:
            partners = rng.integers(0, N_USERS, N_USERS)
            k_sp = cur[partners]
            rows = np.arange(N_USERS)
            tau[rows, k_sp] += WOM * (tau[partners, k_sp] - tau[rows, k_sp])
        # honest index learns from its panel's FULL trace (ads included)
        if honest_present:
            panel = cur == 1
            if panel.any():
                sums = np.bincount(buy[panel], weights=s[panel], minlength=M_SELLERS)
                cnts = np.bincount(buy[panel], minlength=M_SELLERS)
                nz = cnts > 0
                mean_s = np.zeros(M_SELLERS)
                mean_s[nz] = sums[nz] / cnts[nz]
                w = cnts / (cnts + QHAT_PRIOR_N)
                q_hat = (1 - w) * q_hat + w * mean_s
        # --- seller economics & evolution ---
        sales = np.bincount(buy, minlength=M_SELLERS)
        profit = sales * MARGIN / (N_USERS / M_SELLERS) - 1.0
        profit_ema = 0.95 * profit_ema + 0.05 * profit
        q = np.clip(q + Q_GROW * alloc[:, 0] * (1 - q) - Q_DEP * q, 0, 1)
        if (t + 1) % IMIT_EVERY == 0:
            peer = rng.integers(0, M_SELLERS, M_SELLERS)
            better = profit_ema[peer] > profit_ema
            new_alloc = alloc.copy()
            new_alloc[better] = (IMIT_COPY * alloc[peer[better]]
                                 + (1 - IMIT_COPY) * alloc[better])
            noise = rng.dirichlet([30, 30, 30], M_SELLERS)
            new_alloc = 0.9 * new_alloc + 0.1 * noise
            alloc = new_alloc / new_alloc.sum(1, keepdims=True)
        if record_traj and t % 2 == 0:
            traj["hon_share"].append(float((cur == 1).mean()))
            traj["qbar"].append(float(q.mean()))
            traj["w_bribe"].append(float(alloc[:, 1].mean()))
            traj["tau_inc"].append(float(tau[:, 0].mean()))
            traj["share_inc"].append(float((cur == 0).mean()))
    out = dict(hon_share_T=float((cur == 1).mean()),
               qbar_T=float(q.mean()),
               w_bribe_T=float(alloc[:, 1].mean()))
    if record_traj:
        out["traj"] = traj
    return out


def main():
    ns, nl = len(STICKINESS_AXIS), len(TRUST_LR_AXIS)
    hon_share = np.zeros((ns, nl))
    dq = np.zeros((ns, nl))
    wbribe = np.zeros((ns, nl))
    # counterfactual: no honest index (axes irrelevant)
    q_cf = [run(0, 0.02, s, honest_present=False)["qbar_T"] for s in SEEDS]
    print("counterfactual qbar_T per seed:", [round(x, 4) for x in q_cf])
    for i, st in enumerate(STICKINESS_AXIS):
        for j, lr in enumerate(TRUST_LR_AXIS):
            hs, qb, wb = [], [], []
            for k, s in enumerate(SEEDS):
                r = run(st, lr, s)
                hs.append(r["hon_share_T"])
                qb.append(r["qbar_T"] - q_cf[k])
                wb.append(r["w_bribe_T"])
            hon_share[i, j] = np.mean(hs)
            dq[i, j] = np.mean(qb)
            wbribe[i, j] = np.mean(wb)
        print(f"stickiness={st}: hon_share={np.round(hon_share[i], 2).tolist()}")
    # sigma robustness slice at (1.5, 0.04)
    sig_res = {}
    for sig in [0.15, 0.25, 0.35]:
        sig_res[sig] = float(np.mean([run(1.5, 0.04, s, sigma_out=sig)["hon_share_T"]
                                      for s in SEEDS]))
    print("sigma slice at (1.5, 0.04):", sig_res)
    # showcase trajectories: one honest-win cell, one incumbent-hold cell
    show = {}
    for name, (st, lr) in {"win": (0.5, 0.08), "hold": (3.0, 0.01)}.items():
        show[name] = run(st, lr, SEEDS[0], record_traj=True)["traj"]
    cf_traj = run(0, 0.02, SEEDS[0], honest_present=False, record_traj=True)["traj"]

    # ---------- figures ----------
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, mat, title, cmap in [
            (axes[0], hon_share, "E1: доля честного индекса на T", "viridis"),
            (axes[1], dq, "E2: Δq̄ против контрфакта", "RdBu_r")]:
        vmax = 1.0 if mat is hon_share else max(1e-3, np.abs(mat).max())
        vmin = 0.0 if mat is hon_share else -vmax
        im = ax.imshow(mat, origin="lower", aspect="auto",
                       cmap=cmap, vmin=vmin, vmax=vmax)
        if mat is hon_share:
            ax.contour(mat, levels=[0.5], colors="w", linewidths=2)
        ax.set_xticks(range(nl), [str(x) for x in TRUST_LR_AXIS])
        ax.set_yticks(range(ns), [str(x) for x in STICKINESS_AXIS])
        ax.set_xlabel("trust_lr")
        ax.set_ylabel("default_stickiness")
        ax.set_title(title)
        fig.colorbar(im, ax=ax)
    fig.suptitle("EXP-BALANCE-001 — фазовые карты (среднее по 3 сидам)")
    fig.tight_layout()
    fig.savefig("phase_maps.png", dpi=150)

    fig2, ax = plt.subplots(2, 2, figsize=(12, 8))
    tt = np.arange(len(show["win"]["hon_share"])) * 2
    ax[0, 0].plot(tt, show["win"]["hon_share"], label="победа (0.5, 0.08)")
    ax[0, 0].plot(tt, show["hold"]["hon_share"], label="дефолты держат (3.0, 0.01)")
    ax[0, 0].set_title("Доля честного индекса")
    ax[0, 0].legend()
    ax[0, 1].plot(tt, show["win"]["qbar"], label="с честным (победа)")
    ax[0, 1].plot(tt, show["hold"]["qbar"], label="с честным (дефолты)")
    ax[0, 1].plot(tt, cf_traj["qbar"], "--", label="контрфакт (без честного)")
    ax[0, 1].set_title("Среднее качество рынка q̄(t)")
    ax[0, 1].legend()
    ax[1, 0].plot(tt, show["win"]["w_bribe"], label="победа")
    ax[1, 0].plot(tt, show["hold"]["w_bribe"], label="дефолты")
    ax[1, 0].plot(tt, cf_traj["w_bribe"], "--", label="контрфакт")
    ax[1, 0].set_title("E3: средняя доля взяток в аллокациях")
    ax[1, 0].legend()
    ax[1, 1].plot(tt, show["win"]["tau_inc"], label="доверие инкумбенту (победа)")
    ax[1, 1].plot(tt, show["win"]["share_inc"], label="доля инкумбента (победа)")
    ax[1, 1].plot(tt, show["hold"]["tau_inc"], "--", label="доверие (дефолты)")
    ax[1, 1].plot(tt, show["hold"]["share_inc"], "--", label="доля (дефолты)")
    ax[1, 1].set_title("E4: зазор доверие–доля инкумбента")
    ax[1, 1].legend(fontsize=8)
    for a in ax.flat:
        a.set_xlabel("тик")
    fig2.suptitle("EXP-BALANCE-001 — траектории (сид 11)")
    fig2.tight_layout()
    fig2.savefig("trajectories.png", dpi=150)

    json.dump({"hon_share": hon_share.tolist(), "dq": dq.tolist(),
               "w_bribe": wbribe.tolist(), "sigma_slice": sig_res,
               "q_cf": q_cf, "stickiness_axis": STICKINESS_AXIS,
               "trust_lr_axis": TRUST_LR_AXIS},
              open("results_001.json", "w"), indent=1)
    print("done")


if __name__ == "__main__":
    main()
