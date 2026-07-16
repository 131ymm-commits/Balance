"""EXP-BALANCE-004 — performative forecasting with a deflated frame.

The predictor publishes a TARGET forecast (share+push) to steer the system,
not to describe it. We measure causal lift (published vs silent counterfactual),
the ceiling of self-fulfilment (does an unreachable target arrive?), and
punishment of over-promising (pred_trust decay). Accuracy of a self-fulfilling
forecast is undefined by design; we do not report it. Pre-registered PREREG_004.
"""
import sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from spectral import change_op, blanket_diag

N_USERS = 400; M_SELLERS = 24; SEEDS = [11, 22, 33]
BETA = 6.0; C_SWITCH = 1.50; WOM = 0.02; EPS_EXPLORE = 0.02
RECONSIDER = 0.20; SIGMA_OUT = 0.25
Q_GROW = 0.010; Q_DEP = 0.004; MARGIN = 0.40
IMIT_EVERY = 20; IMIT_COPY = 0.8; TEMP = 0.10
W_BRIBE_RANK = 0.7; W_Q_RANK = 0.3; Q_NOISE_INC = 0.15
QHAT_PRIOR_N0 = 20.0; ADS_PROB_MAX = 0.15
HIST_MIN = 120; H = 30; T_PUB = 40; FOCAL_BASE = 2.0


def softmax(x, temp=TEMP):
    z = (x - x.max()) / temp; e = np.exp(z); return e / e.sum()


def build_neighbors(rng, n):
    idx = np.arange(n)
    cols = [np.roll(idx, s) for s in (-4, -3, -2, -1, 1, 2, 3, 4)]
    extra = rng.integers(0, n, n); extra = np.where(extra == idx, (extra + 1) % n, extra)
    return np.stack(cols + [extra], axis=1)


def run(seed, push, mode, T=1600, seed_frac=0.05,
        stickiness=1.0, trust_lr=0.04, eta=1.0, k_audit=10):
    rng = np.random.default_rng(seed)
    q = rng.uniform(0.35, 0.75, M_SELLERS); q_hist_mean = q.mean()
    alloc = rng.dirichlet([1.5, 3.0, 1.5], M_SELLERS)
    profit_ema = np.zeros(M_SELLERS); q_hat = np.full(M_SELLERS, 0.5)
    cur = np.zeros(N_USERS, dtype=int)
    tau = np.stack([np.full(N_USERS, 0.60), np.full(N_USERS, 0.40)], axis=1)
    neigh = build_neighbors(rng, N_USERS)
    is_seed = np.zeros(N_USERS, dtype=bool)
    if seed_frac > 0:
        sid = rng.choice(N_USERS, int(N_USERS * seed_frac), replace=False)
        cur[sid] = 1; tau[sid, 1] = 0.60; is_seed[sid] = True
    rows = np.arange(N_USERS)
    share_trace = np.empty(T)
    macro_hist = []
    target_pred = 0.0; pred_trust = 0.5
    pending = []
    for t in range(T):
        share = (cur == 1).mean()
        macro_hist.append([share, tau[:, 1].mean(), q.mean(), alloc[:, 1].mean()])
        still = []
        for (rt, published_val) in pending:
            if rt == t:
                gap = abs(published_val - share)
                pred_trust = float(np.clip(pred_trust + 0.3 * (0.1 - gap) / 0.1, 0.0, 1.0))
            elif rt > t: still.append((rt, published_val))
        pending = still
        if t % T_PUB == 0 and len(macro_hist) >= HIST_MIN:
            target_pred = min(1.0, share + push)   # ambitious target
            pending.append((t + H, target_pred))
        recon = rng.random(N_USERS) < RECONSIDER
        d = BETA * (tau[:, 1] - tau[:, 0]); leave_bias = eta * is_seed
        # performative: focal steers toward target, scaled by predictor trust
        focal_term = (FOCAL_BASE * pred_trust * (target_pred - share)
                      if mode == "published" else 0.0)
        p_to_hon = 1.0 / (1.0 + np.exp(-(d - C_SWITCH - stickiness + focal_term)))
        p_to_inc = 1.0 / (1.0 + np.exp(-(-d - C_SWITCH - leave_bias - focal_term)))
        u = rng.random(N_USERS)
        go_hon = recon & (cur == 0) & (u < p_to_hon)
        go_inc = recon & (cur == 1) & (u < p_to_inc)
        cur[go_hon] = 1; cur[go_inc] = 0
        if k_audit > 0 and go_hon.any():
            na = int(go_hon.sum()); virt = q_hist_mean + rng.normal(0, SIGMA_OUT, (na, k_audit))
            for j in range(k_audit):
                tau[go_hon, 1] = np.clip(tau[go_hon, 1] + trust_lr * (virt[:, j] - tau[go_hon, 1]), 0, 1)
        inc_score = (W_BRIBE_RANK * alloc[:, 1] / (alloc[:, 1].mean() + 1e-9)
                     + W_Q_RANK * (q + rng.normal(0, Q_NOISE_INC, M_SELLERS)))
        p_inc = softmax(inc_score); p_hon = softmax(q_hat)
        buy = np.empty(N_USERS, dtype=int)
        ii = np.where(cur == 0)[0]; ih = np.where(cur == 1)[0]
        if len(ii): buy[ii] = rng.choice(M_SELLERS, len(ii), p=p_inc)
        if len(ih): buy[ih] = rng.choice(M_SELLERS, len(ih), p=p_hon)
        rec_index = cur.copy()
        if len(ii):
            ex = ii[rng.random(len(ii)) < EPS_EXPLORE]
            if len(ex): buy[ex] = rng.choice(M_SELLERS, len(ex), p=p_hon); rec_index[ex] = 1
        ads = alloc[:, 2]; ads_tot = ads.sum()
        if ads_tot > 1e-9:
            p_ad = ADS_PROB_MAX * ads_tot / (ads_tot + M_SELLERS * 0.33)
            au = rng.random(N_USERS) < p_ad
            if au.any(): buy[au] = rng.choice(M_SELLERS, int(au.sum()), p=ads / ads_tot); rec_index[au] = -1
        s = q[buy] + rng.normal(0, SIGMA_OUT, N_USERS)
        for k2 in (0, 1):
            mm = rec_index == k2
            if mm.any(): tau[mm, k2] = np.clip(tau[mm, k2] + trust_lr * (s[mm] - tau[mm, k2]), 0, 1)
        partners = neigh[rows, rng.integers(0, 9, N_USERS)]; ksp = cur[partners]
        tau[rows, ksp] += WOM * (tau[partners, ksp] - tau[rows, ksp])
        panel = cur == 1
        if panel.any():
            sums = np.bincount(buy[panel], weights=s[panel], minlength=M_SELLERS)
            cnts = np.bincount(buy[panel], minlength=M_SELLERS)
            nz = cnts > 0; mean_s = np.zeros(M_SELLERS); mean_s[nz] = sums[nz] / cnts[nz]
            w = cnts / (cnts + QHAT_PRIOR_N0); q_hat = (1 - w) * q_hat + w * mean_s
        sales = np.bincount(buy, minlength=M_SELLERS)
        profit_ema = 0.95 * profit_ema + 0.05 * (sales * MARGIN / (N_USERS / M_SELLERS) - 1.0)
        q = np.clip(q + Q_GROW * alloc[:, 0] * (1 - q) - Q_DEP * q, 0, 1)
        q_hist_mean = 0.98 * q_hist_mean + 0.02 * q[buy].mean()
        if (t + 1) % IMIT_EVERY == 0:
            peer = rng.integers(0, M_SELLERS, M_SELLERS); better = profit_ema[peer] > profit_ema
            na = alloc.copy(); na[better] = IMIT_COPY * alloc[peer[better]] + (1 - IMIT_COPY) * alloc[better]
            noise = rng.dirichlet([30, 30, 30], M_SELLERS); na = 0.9 * na + 0.1 * noise
            alloc = na / na.sum(1, keepdims=True)
        share_trace[t] = (cur == 1).mean()
    return dict(share=share_trace, pred_trust=pred_trust)


def e_hold(share, thr=0.55, need=200):
    ok = share >= thr; r = 0
    for v in ok:
        r = r + 1 if v else 0
        if r >= need: return True
    return False


def main():
    res = {"pub": {}, "sil": {}}
    pushes = [0.05, 0.15, 0.30, 0.60]
    print("=== published vs silent ===")
    for push in pushes:
        pub = [run(s, push, "published") for s in SEEDS]
        sil = [run(s, push, "silent") for s in SEEDS]
        pf = float(np.mean([r["share"][-1] for r in pub]))
        sf = float(np.mean([r["share"][-1] for r in sil]))
        pt = float(np.mean([r["pred_trust"] for r in pub]))
        hold = float(np.mean([e_hold(r["share"]) for r in pub]))
        res["pub"][push] = dict(final=pf, pred_trust=pt, hold=hold,
            traj=np.mean([r["share"] for r in pub], 0)[::10].tolist())
        res["sil"][push] = dict(final=sf)
        print(f"push={push}: published={pf:.3f} silent={sf:.3f} "
              f"lift={pf-sf:+.3f} pred_trust={pt:.2f} hold={hold:.2f}")
    # artifact check for P2: does realized track push linearly with no ceiling?
    reali = [res["pub"][p]["final"] for p in pushes]
    print("realized(push):", [f"{r:.3f}" for r in reali],
          "-> ceiling" if reali[-1] <= reali[-2] + 0.02 else "-> NO ceiling (artifact watch)")
    json.dump(res, open("results_004.json", "w"), indent=1)

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
    ax[0].plot(pushes, [res["pub"][p]["final"] for p in pushes], "o-", label="published")
    ax[0].plot(pushes, [res["sil"][p]["final"] for p in pushes], "s--", label="silent (контрфакт)")
    ax[0].plot(pushes, pushes and [0.318 + 0 for _ in pushes], ":", color="gray", label="стационар ~0.32")
    ax[0].axhline(0.55, color="r", ls=":")
    ax[0].set_xlabel("push (амбиция цели)"); ax[0].set_title("E1/E2: causal lift и потолок")
    ax[0].legend(fontsize=8)
    ax[1].plot(pushes, [res["pub"][p]["pred_trust"] for p in pushes], "o-", color="purple")
    ax[1].set_xlabel("push"); ax[1].set_ylabel("финальное доверие предиктору")
    ax[1].set_title("E3: наказание за переобещание")
    for push in [0.15, 0.60]:
        tt = np.arange(len(res["pub"][push]["traj"])) * 10
        ax[2].plot(tt, res["pub"][push]["traj"], label=f"push={push}")
    ax[2].axhline(0.55, color="r", ls=":"); ax[2].axhline(0.318, color="gray", ls=":")
    ax[2].set_xlabel("тик"); ax[2].set_title("Траектории published"); ax[2].legend(fontsize=8)
    fig.tight_layout(); fig.savefig("fig_004.png", dpi=150)
    print("done")


if __name__ == "__main__":
    main()
