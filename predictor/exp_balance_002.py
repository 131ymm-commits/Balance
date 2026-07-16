"""EXP-BALANCE-002 — coalitions of architects + spectral predictor.

Cooperative layer over the frozen 001d dynamics. Binding coalitions commit
synchronous switches when the spectral predictor forecasts a positive
conditional outcome with sufficient (measured) confidence. Predictor =
SpectralPredictor v15 change_op; confidence = mu_pp order-mass (blanket_diag).
Pre-registered PREREG_002. Single run, no calibration.
"""
import sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from spectral import change_op, blanket_diag

N_USERS = 400
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
PRED_R = 4          # spectral rank for predictor
HIST_MIN = 120      # ticks of macro-history before predictor is usable
H = 30              # forecast horizon
T_COMMIT = 40       # coalition attempts every T_COMMIT ticks


def softmax(x, temp=TEMP):
    z = (x - x.max()) / temp
    e = np.exp(z)
    return e / e.sum()


def build_neighbors(rng, n):
    idx = np.arange(n)
    cols = [np.roll(idx, s) for s in (-4, -3, -2, -1, 1, 2, 3, 4)]
    extra = rng.integers(0, n, n)
    extra = np.where(extra == idx, (extra + 1) % n, extra)
    return np.stack(cols + [extra], axis=1)


def predictor_forecast(hist, cur_share, delta_share, r=PRED_R, h=H):
    """Conditional forecast: from a counterfactual state where coalition raised
    honest share by delta_share, roll change_op h steps. Returns predicted
    honest-share at horizon and measured confidence (mu_pp order-mass)."""
    Z = np.asarray(hist, float)
    Zc = (Z - Z.mean(0)) / (Z.std(0) + 1e-9)
    mu, sd = Z.mean(0), Z.std(0) + 1e-9
    D = change_op(Zc, r)
    order = blanket_diag(Zc, r)[0]
    # counterfactual current state (normalized): bump share component (index 0)
    state = (Z[-1].copy())
    state[0] = min(1.0, cur_share + delta_share)
    s = (state - mu) / sd
    for _ in range(h):
        s = s + D @ s
    pred = np.clip(s * sd + mu, 0, 1)
    return float(pred[0]), float(order)


def run(seed, coord, conf_min, max_coal, T=1600, seed_frac=0.05,
        stickiness=1.0, trust_lr=0.04, eta=1.0, k_audit=10):
    rng = np.random.default_rng(seed)
    q = rng.uniform(0.35, 0.75, M_SELLERS)
    q_hist_mean = q.mean()
    alloc = rng.dirichlet([1.5, 3.0, 1.5], M_SELLERS)
    profit_ema = np.zeros(M_SELLERS)
    q_hat = np.full(M_SELLERS, 0.5)
    cur = np.zeros(N_USERS, dtype=int)
    tau = np.stack([np.full(N_USERS, 0.60), np.full(N_USERS, 0.40)], axis=1)
    neigh = build_neighbors(rng, N_USERS)
    is_seed = np.zeros(N_USERS, dtype=bool)
    if seed_frac > 0:
        sid = rng.choice(N_USERS, int(N_USERS * seed_frac), replace=False)
        cur[sid] = 1
        tau[sid, 1] = 0.60
        is_seed[sid] = True
    rows = np.arange(N_USERS)
    share_trace = np.empty(T)
    macro_hist = []
    calib = []   # (predicted_share_at_H, realized_share_at_H, confidence)
    pending = []  # (realize_tick, predicted, confidence)
    for t in range(T):
        share = (cur == 1).mean()
        macro_hist.append([share, tau[:, 1].mean(), q.mean(), alloc[:, 1].mean()])
        # resolve matured predictions for calibration
        still = []
        for (rt, pr, cf) in pending:
            if rt == t:
                calib.append((pr, share, cf))
            elif rt > t:
                still.append((rt, pr, cf))
        pending = still
        # ---- coalition step ----
        if coord and t % T_COMMIT == 0 and len(macro_hist) >= HIST_MIN and share < 0.99:
            hist = np.array(macro_hist[-HIST_MIN:])
            inc_users = np.where(cur == 0)[0]
            if len(inc_users) > 5:
                m = min(int(N_USERS * max_coal), len(inc_users))
                delta = m / N_USERS
                pred_share, conf = predictor_forecast(hist, share, delta)
                # coalition commits iff predicted collective gain AND confident
                if pred_share > share + 0.01 and conf >= conf_min:
                    chosen = rng.choice(inc_users, m, replace=False)
                    cur[chosen] = 1
                    # binding: give them retro-audit boost so it's a real move
                    if k_audit > 0:
                        virt = q_hist_mean + rng.normal(0, SIGMA_OUT, (m, k_audit))
                        for j in range(k_audit):
                            tau[chosen, 1] = np.clip(
                                tau[chosen, 1] + trust_lr * (virt[:, j] - tau[chosen, 1]), 0, 1)
                    pending.append((t + H, pred_share, conf))
        # ---- individual switching (frozen 001d) ----
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
                tau[go_hon, 1] = np.clip(tau[go_hon, 1] + trust_lr * (virt[:, j] - tau[go_hon, 1]), 0, 1)
        inc_score = (W_BRIBE_RANK * alloc[:, 1] / (alloc[:, 1].mean() + 1e-9)
                     + W_Q_RANK * (q + rng.normal(0, Q_NOISE_INC, M_SELLERS)))
        p_inc = softmax(inc_score)
        p_hon = softmax(q_hat)
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
        partners = neigh[rows, rng.integers(0, 9, N_USERS)]
        ksp = cur[partners]
        tau[rows, ksp] += WOM * (tau[partners, ksp] - tau[rows, ksp])
        panel = cur == 1
        if panel.any():
            sums = np.bincount(buy[panel], weights=s[panel], minlength=M_SELLERS)
            cnts = np.bincount(buy[panel], minlength=M_SELLERS)
            nz = cnts > 0; mean_s = np.zeros(M_SELLERS); mean_s[nz] = sums[nz] / cnts[nz]
            w = cnts / (cnts + QHAT_PRIOR_N0)
            q_hat = (1 - w) * q_hat + w * mean_s
        sales = np.bincount(buy, minlength=M_SELLERS)
        profit = sales * MARGIN / (N_USERS / M_SELLERS) - 1.0
        profit_ema = 0.95 * profit_ema + 0.05 * profit
        q = np.clip(q + Q_GROW * alloc[:, 0] * (1 - q) - Q_DEP * q, 0, 1)
        q_hist_mean = 0.98 * q_hist_mean + 0.02 * q[buy].mean()
        if (t + 1) % IMIT_EVERY == 0:
            peer = rng.integers(0, M_SELLERS, M_SELLERS)
            better = profit_ema[peer] > profit_ema
            na = alloc.copy(); na[better] = IMIT_COPY * alloc[peer[better]] + (1 - IMIT_COPY) * alloc[better]
            noise = rng.dirichlet([30, 30, 30], M_SELLERS)
            na = 0.9 * na + 0.1 * noise; alloc = na / na.sum(1, keepdims=True)
        share_trace[t] = (cur == 1).mean()
    return dict(share=share_trace, calib=calib)


def e_hold(share, thr=0.55, need=200):
    ok = share >= thr; r = 0
    for v in ok:
        r = r + 1 if v else 0
        if r >= need: return True
    return False


def main():
    res = {"grid": {}, "calib_all": []}
    print("=== control: coord OFF ===")
    off = [run(s, False, 0.0, 0.20) for s in SEEDS]
    off_share = float(np.mean([r["share"][-1] for r in off]))
    print(f"coord OFF: final={off_share:.3f} (expect ~0.30, reproduces 001d)")
    res["coord_off"] = off_share
    print("=== coord ON grid ===")
    for cm in [0.0, 0.2, 0.4]:
        for mc in [0.05, 0.20, 0.50]:
            tr = [run(s, True, cm, mc) for s in SEEDS]
            fin = float(np.mean([r["share"][-1] for r in tr]))
            hold = np.mean([e_hold(r["share"]) for r in tr])
            for r in tr: res["calib_all"].extend(r["calib"])
            res["grid"][f"{cm}_{mc}"] = dict(final=fin, hold=float(hold),
                traj=np.mean([r["share"] for r in tr], 0)[::10].tolist())
            print(f"conf_min={cm} max_coal={mc}: final={fin:.3f} hold={hold:.2f}")
    # calibration analysis
    ca = np.array(res["calib_all"])
    if len(ca):
        pred, real, conf = ca[:, 0], ca[:, 1], ca[:, 2]
        err = np.abs(pred - real)
        res["calibration"] = dict(
            n=len(ca), mae=float(err.mean()),
            hit_005=float((err <= 0.05).mean()),
            hit_010=float((err <= 0.10).mean()),
            corr_pred_real=float(np.corrcoef(pred, real)[0, 1]) if len(ca) > 2 else None,
            corr_conf_err=float(np.corrcoef(conf, err)[0, 1]) if len(ca) > 2 else None)
        print("=== E3 predictor calibration ===")
        print(f"  n={len(ca)} MAE={err.mean():.3f} hit±0.05={ (err<=0.05).mean():.2f} "
              f"hit±0.10={(err<=0.10).mean():.2f}")
        print(f"  corr(pred,real)={res['calibration']['corr_pred_real']} "
              f"corr(conf,err)={res['calibration']['corr_conf_err']}")
    json.dump(res, open("results_002.json", "w"), indent=1)

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
    for mc, mk in [(0.05, "o-"), (0.20, "s-"), (0.50, "^-")]:
        cms = [0.0, 0.2, 0.4]
        ax[0].plot(cms, [res["grid"][f"{cm}_{mc}"]["final"] for cm in cms], mk, label=f"coal≤{int(mc*100)}%")
    ax[0].axhline(off_share, color="gray", ls=":", label="coord OFF")
    ax[0].axhline(0.55, color="r", ls=":", label="порог E_hold")
    ax[0].set_xlabel("conf_min"); ax[0].set_title("E1/E2: финал vs порог уверенности")
    ax[0].legend(fontsize=8)
    for key in ["0.0_0.5", "0.2_0.5", "0.0_0.05"]:
        tt = np.arange(len(res["grid"][key]["traj"])) * 10
        ax[1].plot(tt, res["grid"][key]["traj"], label=key)
    ax[1].axhline(0.55, color="r", ls=":"); ax[1].axhline(off_share, color="gray", ls=":")
    ax[1].set_xlabel("тик"); ax[1].set_title("Траектории"); ax[1].legend(fontsize=8)
    if len(ca):
        ax[2].scatter(pred, real, s=8, alpha=0.4)
        ax[2].plot([0, 1], [0, 1], "k--", lw=1)
        ax[2].set_xlabel("предсказано"); ax[2].set_ylabel("реализовано")
        ax[2].set_title(f"E3 калибровка (MAE={err.mean():.3f})")
        ax[2].set_xlim(0, 1); ax[2].set_ylim(0, 1)
    fig.tight_layout(); fig.savefig("fig_002.png", dpi=150)
    print("done")


if __name__ == "__main__":
    main()
