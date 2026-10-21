"""XCHECK-001 — closed-form null model vs the frozen 002c stand.

Claim under test: with trust gap d ~ 0, each user is a two-state Markov chain
with per-tick rates sig(-B_in) and sig(-B_out), so the stationary honest share
is fixed by the barrier asymmetry alone; coalitions and the predictor are only
the vehicle that lowers B_in permanently. Pre-registered PREREG_XCHECK-001.
exp_balance_002c.py is imported unchanged; one run per config, no calibration.
"""
import json, types
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import exp_balance_002c as base

SEEDS = base.SEEDS
T = 1600
TAIL = T // 4          # last quarter: ticks 1200..1599
B_FULL = base.C_SWITCH + 1.0   # C_SWITCH + stickiness=1.0 (frozen 002c default)
TOL = 0.03


def sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def closed_form(s, d=0.0, f=0.05, eta=1.0):
    """Stationary honest share: entry barrier B_FULL*(1-s), exit C_SWITCH (+eta for seeds)."""
    p_in = sig(d - B_FULL * (1.0 - s))
    p_out = sig(-d - base.C_SWITCH)
    p_out_seed = sig(-d - base.C_SWITCH - eta)
    return float((1 - f) * p_in / (p_in + p_out) + f * p_in / (p_in + p_out_seed))


def instrumented_run():
    """Textual copy of base.run that also records mean trust gap d per tick."""
    src = open(base.__file__, encoding="utf-8").read()
    a = "    share_trace = np.empty(T)\n"
    b = "        share_trace[t] = (cur == 1).mean()\n"
    c = "    return dict(share=share_trace, calib=calib)\n"
    assert src.count(a) == src.count(b) == src.count(c) == 1
    src = src.replace(a, a + "    d_trace = np.empty(T)\n")
    src = src.replace(b, b + "        d_trace[t] = d.mean()\n")
    src = src.replace(c, "    return dict(share=share_trace, calib=calib, d=d_trace)\n")
    mod = types.ModuleType("exp_balance_002c_instrumented")
    exec(compile(src, "exp_balance_002c_instrumented", "exec"), mod.__dict__)
    return mod.run


def summarize(runs):
    return dict(
        tail=float(np.mean([r["share"][-TAIL:].mean() for r in runs])),
        final=float(np.mean([r["share"][-1] for r in runs])),
        hold=float(np.mean([base.e_hold(r["share"]) for r in runs])),
        d_tail=float(np.mean([r["d"][-TAIL:].mean() for r in runs])),
        tail_per_seed=[float(r["share"][-TAIL:].mean()) for r in runs],
        traj=np.mean([r["share"] for r in runs], 0)[::10].tolist())


def main():
    run_i = instrumented_run()
    res = {"tol": TOL, "configs": {}}

    # ---- integrity gate: instrumentation must not change the dynamics ----
    print("=== gate: instrumented copy == frozen 002c (infection=0, s=0.9) ===")
    orig = [base.run(s, True, 0.9, 0.0) for s in SEEDS]
    inst = [run_i(s, True, 0.9, 0.0) for s in SEEDS]
    identical = all(np.array_equal(o["share"], i["share"]) for o, i in zip(orig, inst))
    pub = json.load(open("results/results_002c.json"))["grid"]["0.0_0.9"]["traj"]
    matches_pub = bool(np.allclose(np.mean([o["share"] for o in orig], 0)[::10], pub))
    res["gate"] = dict(identical_to_original=identical, matches_published=matches_pub)
    print(f"identical={identical} matches_published={matches_pub}")
    if not (identical and matches_pub):
        json.dump(res, open("results_xcheck_001.json", "w"), indent=1)
        raise SystemExit("gate failed: stopping per PREREG_XCHECK-001 §5")

    def record(key, kind, s, runs):
        sm = summarize(runs)
        sm.update(kind=kind, s=s, closed_form=closed_form(s),
                  err=sm["tail"] - closed_form(s) if s is not None else None)
        res["configs"][key] = sm
        cf = f"cf={sm['closed_form']:.3f} err={sm['err']:+.3f}" if s is not None else ""
        print(f"{key:>14}: tail={sm['tail']:.3f} final={sm['final']:.3f} "
              f"hold={sm['hold']:.2f} d={sm['d_tail']:+.3f} {cf}")

    print("=== P0/P1: coalition dose-response (infection=0) ===")
    record("coal_0.9", "coalition", 0.9, inst)
    for s in [0.2, 0.4, 0.6, 0.8, 1.0]:
        record(f"coal_{s}", "coalition", s, [run_i(sd, True, s, 0.0) for sd in SEEDS])

    print("=== P2: no coalition, no predictor, global permanent entry-barrier cut ===")
    for s in [0.6, 0.9]:
        st = B_FULL * (1.0 - s) - base.C_SWITCH
        record(f"global_{s}", "global_cut", s,
               [run_i(sd, False, 0.0, 0.0, stickiness=st) for sd in SEEDS])
    record("control", "control", 0.0, [run_i(sd, False, 0.0, 0.0) for sd in SEEDS])

    # ---- verdicts, exactly as pre-registered ----
    C = res["configs"]
    p0 = all(abs(v["d_tail"]) <= 0.25 for v in C.values())
    p1 = all(abs(C[f"coal_{s}"]["err"]) <= TOL for s in [0.2, 0.4, 0.8, 1.0])
    p2 = all(abs(C[f"global_{s}"]["err"]) <= TOL
             and abs(C[f"global_{s}"]["tail"] - C[f"coal_{s}"]["tail"]) <= TOL
             for s in [0.6, 0.9])
    res["verdict"] = dict(P0=p0, P1=p1, P2=p2)
    print(f"verdict: P0={p0} P1={p1} P2={p2}")
    json.dump(res, open("results_xcheck_001.json", "w"), indent=1)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ss = np.linspace(0, 1, 101)
    ax[0].plot(ss, [closed_form(s) for s in ss], "k-", lw=1, label="формула (d=0)")
    old = json.load(open("results/results_002c.json"))["grid"]
    ax[0].plot([0.0, 0.6, 0.9], [np.mean(old[f"0.0_{s}"]["traj"][120:]) for s in [0.0, 0.6, 0.9]],
               "o", mfc="none", ms=10, label="002c опубликовано (ретродикция)")
    pts = [0.2, 0.4, 0.8, 1.0]
    ax[0].plot(pts, [C[f"coal_{s}"]["tail"] for s in pts], "s", label="коалиция, новые s (P1)")
    ax[0].plot([0.6, 0.9], [C[f"global_{s}"]["tail"] for s in [0.6, 0.9]], "^",
               ms=9, label="без коалиции, глобальный барьер (P2)")
    ax[0].axhline(0.55, color="r", ls=":", label="линия E_hold")
    ax[0].set_xlabel("s (снижение барьера входа)"); ax[0].set_ylabel("доля честного, посл. четверть")
    ax[0].set_title("XCHECK-001: доза-ответ"); ax[0].legend(fontsize=8)
    for key in ["coal_0.9", "global_0.9", "coal_0.4", "control"]:
        tt = np.arange(len(C[key]["traj"])) * 10
        ax[1].plot(tt, C[key]["traj"], label=key)
    ax[1].axhline(0.55, color="r", ls=":")
    ax[1].set_xlabel("тик"); ax[1].set_title("Траектории"); ax[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig("fig_xcheck_001.png", dpi=150)
    print("done")


if __name__ == "__main__":
    main()
