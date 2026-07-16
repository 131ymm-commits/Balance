# Balance — The Un-Buyable Recommender

> **A scale you can buy is not a scale.** That is not ethics; it is metrology — a bought instrument measures its buyer's wishes, not the world. Balance is a recommender that structurally cannot be bought: products ranked by realized outcomes (repeat purchases, returns, churn), computed privately on the user's own device, monetized by selling sellers the truth about their own performance — never placement.

**Полный манифест — вся идея в одном файле: [MANIFESTO.md](MANIFESTO.md)** *(RU; краткое зеркало — [docs/MANIFESTO_ru.md](docs/MANIFESTO_ru.md); исследовательские документы частично на русском).*

---

## What this is

Strip the philosophy and a known business remains: a retail outcome panel — the product NielsenIQ and Circana sell for billions — rebuilt at software cost, live instead of quarterly, per-product instead of per-segment, delivered through the user's own agent instead of a dashboard. The philosophy is what assembles the asset: the panel consists of people who consented precisely because the instrument cannot be bought.

Two channels, both honest: a **disclosed paid visibility** channel ("Acme paid $X to appear here" — the amount and the name), and an **un-buyable outcome rank** that is not for sale at any price. Disclosure kills deception; the un-buyable rank kills corruption.

Full design: [docs/PROPOSAL_anthropic_v2_1.md](docs/PROPOSAL_anthropic_v2_1.md) (English, post-review v2.1). Conceptual lineage and what is actually new: [docs/PRIOR_ART.md](docs/PRIOR_ART.md).

## Status and headline result

This repository contains the concept **plus a falsifiable test stand that was required, by its own design, to be able to prove the concept wrong** — and did so seven times before saying one reproducible "yes".

> **Headline finding.** In a closed agent-based market with a bought incumbent holding the default position, the honest outcome index has **no endogenous growth loop** under any of: time (×8 horizon), seeding (2–20%), cohort retention, onboarding retro-audit, signal-side network effects, coalition stimulus, Schelling focal forecasts, or performative forecasting. It converges to a ~30% stationary share. **Exactly one mechanism breaks through and holds: an *irreversible* reduction of the switching cost** (a coalition move that permanently removes the risk of being the lone switcher). Result: stable 0.61–0.71 share, reproduced on **5/5 fresh seeds**. Everything else — network contagion, performative forecasts — is an accelerant, not an engine.

Translated to product terms: adoption is not "build it and they will come"; it is a threshold condition. Make leaving the incumbent irreversible *by reason, not by lock* (personal purchase-history and retro-audit migrate with the user; a collective switch removes loneliness risk permanently), and the honest index grows. The specification replaced the hope.

## The research program

Every experiment was **pre-registered before running**, with named predictions; every negative is published as a primary result; failed calibrations and one implementation bug are archived openly (see Integrity record).

### Stand arc (`stand/`) — does the honest index survive a bought incumbent?

| Exp | Question | Verdict |
|---|---|---|
| **001** | Phase "accuracy vs defaults" over (stickiness × trust-speed) | No accuracy-wins phase anywhere on the grid; binding constraint is the *epistemic clock* — how a non-user learns the alternative is accurate — not the incumbent's defense |
| **001b** | Time (×8 horizon), seeding, reinvestment flywheel | Stationary state immune to horizon; seeded cohorts assimilate away (retention 0.22–0.33 ≈ background); the flywheel amplifies *any* leader — honest share 0.29→0.02 at low trust-speed; market collapses to monoculture without a survival floor |
| **001c** | Retention η, onboarding retro-audit k, survival floor b₀ | Retention holds the cohort (0.33→0.73) yet global share stays ~0.30; floor rescues the market (alive sellers 1→24, mean quality 0.06→0.33); includes a **disclosed sign-bug** and its fix |
| **001d** | Signal-side network effect γ; bifurcation test | γ inert (γ=8 ≈ γ=0); no bistability (start-5% vs start-40% gap = 0.079); the loop is open at *visibility of quality before switching* |

Summary: [stand/STAND_SUMMARY.md](stand/STAND_SUMMARY.md)

### Predictor program (`predictor/`) — coalitions of architects + a spectral predictor

Re-framing (per the project owner): players may coordinate; the predictor issues *conditional* forecasts of agreed changes and **measures its own confidence** instead of declaring it. Engine: the change-operator and Markov-blanket spectral diagnostic extracted from the author's separate SpectralPredictor v15 project ([predictor/spectral.py](predictor/spectral.py)).

| Cycle | Question | Verdict |
|---|---|---|
| **1** (002/003/004) | Coalitions, Schelling focal points, performative forecasts as *stimulus* | All drown in the switching barrier (logit ≈ 2.5). But the predictor behaves honestly: public forecasts calibrated (MAE 0.023, 91% within ±0.05); performative forecasting has a measurable **ceiling of self-fulfilment** and is **punished for over-promising** (predictor trust 1.0→0.0 on unreachable targets) |
| **2** (002b/002c) | Coordination applied to the *barrier* itself | Temporary relief decays back (≤0.347) — same pattern that killed seeding; **irreversible relief breaks through: 0.61–0.71, sustained (E_hold) on all seeds. First "yes" of the program** |
| **3** (003c/004c + repro) | Robustness of the "yes"; Schelling/performative on top | Reproduced **5/5 on new seeds** (finals 0.67–0.745); Schelling adds exactly zero on an inertial forecast; performative adds a small secondary lift (+0.016…+0.026) |

Summary: [predictor/PREDICTOR_PROGRAM_SUMMARY.md](predictor/PREDICTOR_PROGRAM_SUMMARY.md)

## Repository map

```
balance/
├── README.md                  ← you are here
├── MANIFESTO.md               полный манифест — вся идея в одном файле (RU)
├── LICENSE                    MIT
├── requirements.txt           numpy, matplotlib
├── CITATION.cff
├── docs/
│   ├── PROPOSAL_anthropic_v2_1.md   full design (EN, post-review)
│   ├── MANIFESTO_ru.md              манифест (RU, выровнен с v2.1)
│   ├── PRIOR_ART.md                 lineage & what is new (RU)
│   ├── GAME.md                      the test-stand design doc (RU)
│   ├── MVP.md                       one vertical, one metric, kill criteria (RU)
│   └── archive/PROPOSAL_anthropic_v1.md   pre-review version, kept for history
├── stand/                     experiments 001…001d
│   ├── README.md              how to run, file map, integrity notes
│   ├── exp_balance_001_core.py / 001b / 001c / 001c_fix / 001d
│   ├── prereg/                pre-registrations (written BEFORE each run)
│   ├── results/               reports (RU), figures, raw JSON
│   │   └── archive/           failed calibration iterations, published
│   └── STAND_SUMMARY.md
├── predictor/                 cycles 1–3 (coalitions / Schelling / performative)
│   ├── README.md
│   ├── spectral.py            engine extracted from SpectralPredictor v15
│   ├── exp_balance_002.py / 002b / 002c / 003 / 004 / cycle3
│   ├── prereg/  ·  results/
│   └── PREDICTOR_PROGRAM_SUMMARY.md
└── game/                      playable demo layer (React, single-file components)
    ├── BalanceFuture.jsx      future-projection toy
    ├── BalanceMap.jsx         territorial anti-monopoly layer (mock)
    └── BalanceUniverse.jsx    LLM-driven strategic game ("Claude in Claude")
```

## Reproducing the experiments

```bash
pip install -r requirements.txt
cd stand      && python3 exp_balance_001_core.py      # ~1–2 min, writes figures/JSON to CWD
cd ../predictor && python3 exp_balance_002c.py        # the breakthrough experiment
```

All seeds are fixed in the code; committed outputs live in `stand/results/` and `predictor/results/`, so running is optional verification, not a requirement. Scripts write to the current directory. Runtimes: 1–4 minutes each on a laptop-class CPU.

## Integrity record

The stand's own epigraph sets the bar: *"A simulator in which honesty always wins is propaganda with sliders."* Accordingly:

- **11 pre-registrations** written before the corresponding runs, each with named predictions; most predictions were **refuted and are recorded as such** (see the P-sections inside `*/results/RESULTS_*.md`).
- **Failed calibration iterations are archived, not overwritten** (`stand/results/archive/` — iterations 0 and 1 of exp 001).
- **A sign bug** in the retention term of 001c inverted its effect; it was caught by its own nonsensical output, disclosed with diagnostics, and both the buggy and fixed runs are published side by side (`exp_balance_001c.py` deliberately preserves the bug; `exp_balance_001c_fix.py` fixes only the sign).
- **Stopping rules** limited calibration to two documented iterations per experiment; when they fired, the negative was published as the main result.
- The single positive result was **stress-tested on 5 independent seeds** before being claimed.

## The playable layer

`docs/GAME.md` specifies two firewalled builds: the **stand** (headless, pre-registered parameters, publishes the regimes where we lose — that is `stand/` and `predictor/` here) and the **game** (playable, legible defaults, mandatory worst-case mode). The `game/` folder holds early playable prototypes of the second build; they are recruiting/vision artifacts, not evidence.

## Conceptual lineage (credited in full in docs/PRIOR_ART.md)

Polycentric governance, distributed monitoring, graduated sanctions — **Elinor Ostrom**; the proven un-buyable rating model — **Yuka**; outcome-signal validity — retail panel research (NielsenIQ/Circana lineage); trace access — **PSD2 open banking, GDPR portability**; governance lessons — **the Linux kernel and its foundation model**; the stand's game-theoretic core — **Axelrod; Nowak–Sigmund; Noë–Hammerstein; Klemperer** (switching costs / default effects); focal points — **Schelling**; performativity — **Soros; MacKenzie**; the spectral engine — **Koopman / DMD, ResDMD residuals (Colbrook)** via the author's SpectralPredictor v15.

## License, citation, contact

MIT for code and research (see [LICENSE](LICENSE)); the fiction layer in `game/` is CC BY-SA 4.0 ([game/LICENSE-FICTION.md](game/LICENSE-FICTION.md)) — the open canon is open by license, not by mood. Cite via [CITATION.cff](CITATION.cff).
Author: **131ym** — GitHub [@131ymm-commits](https://github.com/131ymm-commits) · Independent researcher, Germany.

> *Status: hypotheses, not truths. Open; forking is legitimate and expected; there is no center.*
