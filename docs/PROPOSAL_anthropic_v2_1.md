# The Un-Buyable Recommender

### Proposal to Anthropic · Balance — v2.1

> **A scale you can buy is not a scale.** That is not ethics; it is metrology — a bought instrument measures its buyer's wishes, not the world. We propose the one recommender that cannot be bought: ranked by realized outcomes, computed on the user's own device, monetized by selling sellers the truth about their own performance — never placement. It turns Anthropic's ad-free stance from a policy into a product.

---

## 1. What this is, in business terms

Strip the philosophy and a known business remains: a retail outcome panel — the product NielsenIQ and Circana sell for billions — rebuilt at software cost. Panel size in the millions instead of tens of thousands; live instead of quarterly; per-product instead of per-segment; delivered through the user's own agent instead of a dashboard. Sellers already pay heavily for weaker versions of this sight. The philosophy is not decoration on the business; it is what assembles the asset: the panel consists of people who consented precisely because the instrument cannot be bought. Manifesto as recruitment engine; panel as product.

## 2. The problem: there is no neutral information

Every answer to "what should I buy?" points at someone. Answer — you pointed. Stay silent — you left the person to a web where the pointing was bought long ago. The finger is unavoidable; the only question is what it selects for. Today it selects for spend: Goodhart has eaten the market — attention capture has replaced product quality as the optimized metric. The buyer pays in mistakes; the honest maker pays in ad budget that could have been product.

## 3. The rule: un-buyable — attached to the right layer

Un-buyability cannot be promised; it must be structural. And structure must attach to the correct layer. A frontier model is cloud-hosted and closed; a guarantee that depended on it would be rented — and since all revenue is seller-side (§8), the measured party would be funding the measurer. So the design decouples:

- **The measurement layer** — trace collection, private aggregation, index application — is a small, open, statistical component on the user's device. No LLM inside. This layer is the instrument: open source, self-hostable, data local, erased in one click, free of charge to the user forever. It cannot be bought physically, not by pledge.
- **The interface layer** — the agent that talks — is swappable: Claude over an API, a local model, anything. Whose model speaks never touches what the scale reads.

Residual risk, named: a biased interface could misreport an honest index. Mitigation: raw traces stay private, but the index itself is public and deterministic — any interface's output can be diffed against ground truth by anyone, and interfaces are one click to replace.

## 4. Two channels, both honest

- **Disclosed paid visibility.** A seller *may* pay to be seen — labeled radically: **"Acme paid $X to appear here."** The amount and the name, not "sponsored" in gray.
- **The un-buyable outcome rank.** Cannot be bought at all.

Disclosure kills deception; the un-buyable rank kills corruption. Neither channel pretends to be the other — that is the whole trick, and it is what "everything honest" means in practice rather than in slogans.

## 5. The signal: the hardest available proxy

Reviews are gamed because they are declared. The harder signal is what people **did**: bought again, returned, churned — and when. Claimed precisely: **the hardest available proxy, not "no proxy."** Goodhart is not killed; he is relocated — from gaming a public score to gaming the definition of outcome itself. That is why the definition gets a constitution (§6).

Only passively observable events enter the trace. "Still satisfied a year on" is not observable in purchase data; where self-report is used at all, it is labeled as such, optional, and never silently blended into the index.

Extraction is a legal right, not a scrape — with a source hierarchy, because sources differ in what they resolve and how hard they are to forge. EU open banking (PSD2) yields bank-grade truth at merchant level: repeat-at-merchant, subscription churn, timing. Product-level resolution comes from GDPR portability exports and parsed e-receipts — weighted below bank data, because a merchant can spam what it issues but not what the bank records. Every trace event carries its source grade. Computed where it cannot be forged: on the user's device; released only as anonymized aggregates.

## 6. The metric constitution — where Ostrom actually belongs

Repeat is not one signal; its meaning flips by category. Snacks: repeat tracks hyperpalatability, not benefit. Printer ink: phenomenal repeat, hated product — lock-in, not love. A cast-iron pan bought twice is a failure. So outcome functions are per-category, with sign and shape: consumables reward regret-free repeat; durables reward return-free service years; subscriptions reward retention corrected for cancellation friction.

An editorial layer is therefore unavoidable — and an unavoidable editorial layer is either a commons or a capture point. We make it a commons: an open, versioned, forkable **metric constitution**, governed polycentrically — category maintainers, a public RFC process, and the fork as the ultimate check. This, precisely, is Elinor Ostrom's territory (Nobel 2009): a shared resource — the definition of "good" — governed by distributed monitoring and graduated sanctions, the mechanism proven for centuries on real commons.

Two safeguards imported from open-source history. First, every change to an outcome function ships with its **rank-diff** — the published effect of the change on current standings — plus a mandatory review window; a metric edit that reshuffles ranks in someone's favor is a visible diff, not a buried commit. Second, because open process is capturable by whoever pays the maintainers (the kernel's lesson), maintainer funding flows from pooled sight revenue through a foundation with a hard cap on any single payer's share.

**Everything operates in the open, Linux-style:** code, constitution, audit results, aggregate panel demographics, foundation finances, and the cost-of-attack curves below.

## 7. Why honesty scales — arithmetic, then time

Cheating an index is a negative externality on **all** of its users at once: accuracy drops for each of them, on their own outcomes, no collusion required. The sanction is a silent switch to a fork. No verdict; no bribe to prove: **the bribe destroys the asset it bought.**

That handles the crude attack. The precise attack is cheaper: hire real people to make real repeat purchases and nudge rank 4 to rank 1 inside one category. Verifiable personhood does not stop it — a hired human is a person. Arithmetic and time do. Holding a share shift δ in a category with N active panelists costs ~δ·N sustained buyers — *sustained*, because traces decay: not a purchase of rank but a permanent subscription to a lie. At N≈10³ that is dozens of people, cheaper than the ad campaign it replaces — **the young system is the corruptible system; we state it rather than hide it.** At N≈10⁵ it is thousands of coordinated humans, a payroll rivaling honest marketing, and a conspiracy whose leak probability grows with headcount; in the limit the attack degenerates into a price subsidy — nearly honest competition.

Time converts into defense only through mechanism: trace weight grows with account age and purchase diversity; the influence of any statistically correlated cohort is capped; ranks carry confidence intervals, and below a panel-size threshold the honest answer is "not enough data" — which also zeroes the value of marginal shifts, since 4th and 1st inside one interval are the same rank. Product-level cold start is recursive — every new product is born traceless — so young traces are labeled provisional, with a minimum seasoning period; launch windows are the standing target and are treated as such. The per-category cost-of-attack curve is published: security that needs obscurity is not security.

What outcome monitoring cannot see — the bribe that doesn't hurt, a genuinely good product buying placement — the **distributional audit** catches: every index publishes the distribution of its recommendations, and a seller taking 80% of a category's showings with 30% of its good products is visible to anyone with statistics.

These economics are also pre-registered as a falsifiable test stand — an open agent-based game whose published output is the phase surface between "accuracy wins" and "defaults win," required to contain the regimes where we lose, with a second endpoint testing the closing thesis directly: mean market quality with the un-buyable index present versus the counterfactual without it.

## 8. Monetization without corruption: sell sight, never rank

A seller wants three things: to be found, to be measured, and to know why they lost. Sell the third.

- **Sight (the main product):** "here is why you weren't chosen; here is what buyers actually wanted; here is where you lost and won." Real behavior of real customers, anonymized — intelligence that today exists only as lagged, coarse panels, and unlike advertising it **accelerates the market's evolution instead of corrupting it.** Sight is served through the same privacy machinery as the index: sellers query an aggregate engine with a public schema and a bounded privacy budget — never raw traces — and they see the same confidence intervals users see. A revenue product that doubled as a reconstruction attack would spend the panel it lives on.
- **Measurement:** pay to be tested and recorded truthfully; the method is open. You can buy the test — not the score.
- **Disclosed visibility:** priced, labeled with the exact amount, separate from the rank.

**Never sold: a place in the rank. Never charged: the user** — who pays no money and contributes something better, their consented trace, the way Linux users contribute patches.

## 9. Two founders

- **Anthropic: the open base and the stance.** The measurement layer's open code — and, already public, the position that Claude is ad-free, a space to think. Role stated precisely: **creator and maintainer of the open base; optionally one interface among many; never owner of the network or the constitution.** Creator: yes. Center: no.
- **A proven un-buyable rating incumbent (e.g. Yuka): the users.** ~80M users, 6M+ products, brands cannot buy scores, finances published as proof. Its users **self-selected for exactly this value** — and they are contributors, not audience: their own repeats and discards *are* the signal. One conflict disclosed now rather than discovered later: this audience self-selected for **health**, and in food raw repeat rewards hyperpalatability — the exact inversion §6 exists for. So food opens only after its outcome function is ratified through the constitution; the first vertical is household consumables (§13).

Software from one, trust-qualified users from the other. A proposed structure, not a signed one; absent a partnership, the incumbent still stands as proof that the un-buyable model is profitable.

## 10. Competitive landscape — the white space

Every pillar has strong players; **no one holds the intersection.**

- **Agentic commerce** (checkout agents, platform assistants) is seller- or platform-aligned by construction — feeds, conversion, commissions. Bought.
- **Un-buyable ratings** (Yuka; editorially, Consumer Reports) prove the model but score by **proxy or expert test**, in narrow categories, and are not live panels.
- **Outcome signals** (repeat/return) are validated but **locked** in seller dashboards and lagged syndicated panels.
- **Crypto reputation** ranks **identities and attestations, not product outcomes**, and carries token economics we deliberately avoid.
- **Local open agents** are commoditized — which de-risks delivery and means the agent is not the moat.

**The moat is not the index code — code forks in an afternoon. The moat is the consented panel plus the constitution around it:** people who agreed to contribute their trace because of what the instrument refuses to sell. Trust does not fork. Outcome-based × un-buyable × consented-panel × constitution-governed × live × no crypto: each neighbor covers one or two of those; nobody covers six.

## 11. Incumbents are outlasted, not fought

Their revenue is structurally anti-correlated with their value to the user: every paid placement spends trust, the exact asset Balance banks — and they cannot stop, because placement *is* their revenue. As agents mediate purchases, each user experiences the outcome and learns from their own data, no accusation needed. Accuracy diverges along the long trace: one lineage sprints, the other compounds. Speciation, not combat.

**The honest caveat: direction is certain, the clock is not.** Defaults and lock-in sustain decaying products for decades — bought search results have ruled for twenty years. The lever that collapses the clock: **the agent that shows each user their own outcome.** Personally living the divergence is the one thing that beats a default.

## 12. Honest open questions — pre-registered

- **Cold start, twice.** The system's youth is its most corruptible window (§7), and product-level cold start never ends. Fast-churn verticals first; slow domains closed until a real trace exists; the disclosed-visibility channel carries the interim, honestly labeled.
- **Index monopoly = capture.** Guarded hardest: indices cheap, forkable, many; the constitution itself forkable.
- **The bribe that doesn't hurt** is invisible to outcome monitoring; only the distributional audit catches it. Both audits are mandatory.
- **The narrow band.** The goal is deception made expensive, never impossible: total transparency is its own failure mode — no privacy, no room to change. The differential-privacy noise floor enforces the band structurally; the machinery that protects the panel is the same machinery that keeps honesty short of surveillance.
- **Presentation bias.** A dishonest interface reading an honest index — bounded by the index's public determinism and diff-audits (§3), not eliminated.
- **Representativeness.** The panel is self-selected; un-buyable but unrepresentative is still a crooked scale. Aggregate panel demographics are published per category — in tension with privacy aggregates; the tension is managed by thresholds, not denied.
- **Privacy vs the long tail.** Differentially private aggregates on sparse categories yield either leakage or noise; below threshold the answer is "not enough data," and coverage grows with the panel: mass-market first, tail later. Breadth is earned by panel growth, not claimed at launch.
- **The core bet is unproven:** that un-buyable sight beats bought noise for the party paying for results. Strong in gradient; the clock is the risk.

## 13. Minimal first version

One fast-churn vertical: household consumables — detergents, razors, batteries; outcome signal in weeks, no palatability trap. Fork an open local agent for the interface layer; build only the measurement layer. Seed with a trust-qualified cohort whose own repeats bootstrap the index. Sellers pay for sight from day one; never rank; the user pays nothing.

One metric decides everything, and it is not self-graded: **the index, built on cohort A's traces up to time t, must beat review-based baselines at predicting cohort B's repeat behavior after t** — out-of-cohort, out-of-time; secondary independent endpoint: return rates. In-sample prediction of the very repeats the index is made of would be an exam the student wrote. Kill criteria pre-registered; a negative result gets published, not buried.

## 14. Why Anthropic, why now

- **Position:** Claude already holds the trusted-agent seat that recommenders spend fortunes to reach.
- **Alignment:** this is the constructive form of a stance Anthropic already took publicly — ad-free stops being a constraint and becomes the product.
- **Defensibility:** the moat cannot be bought — and the signal it runs on is locked away from consumers today.
- **Timing:** agents are becoming the purchase interface and the defaults have not yet frozen; PSD2 open banking and GDPR portability make the trace a user's legal right in the EU; verifiable personhood is maturing to borrow as one Sybil input (necessary, not sufficient — §7); local agents are commoditized. The window is the user's side of the counter — open now, not forever.

> **We do not abolish advertising. We give it a fitness function — for the first time — and hand the scale to the person it weighs.**

---

*Conceptual base, credited: polycentric governance, distributed monitoring, graduated sanctions — Elinor Ostrom (Nobel 2009); the proven un-buyable rating model — Yuka; outcome-signal validity — retail panel research (NielsenIQ/Circana lineage); trace access — PSD2 open banking and GDPR data portability; governance lessons — the Linux kernel and its foundation model; Sybil resistance — verifiable personhood standards, as one input. Market figures per public industry research.*
