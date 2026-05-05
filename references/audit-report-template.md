# Audit Report Template

Every AI-slop audit produces a report in this format. The structure scales with the verdict — a `PASS` audit can omit the qualitative-violations section; a `CRITICAL` audit needs every section filled.

The audit is structured top-down: verdict first, density score second, top fixes third, then full violation lists, then calibration notes, then the rewrite if requested. Readers should be able to stop reading after the verdict and density and still know what to do.

---

## Template

```markdown
# AI Slop Audit

## Verdict
[PASS / LOW / MEDIUM / HIGH / CRITICAL]

## Density score
- High-severity tells: X per 500 words
- Medium-severity tells: Y per 500 words
- Low-severity tells: Z per 500 words (informational)
- Computed density: D
- Burstiness ratio: 0.X (humans 0.6-1.2, AI 0.2-0.4)
- Likely model fingerprint: [none / GPT / Claude / Gemini / mixed]
- Genre detected: [casual / marketing / academic / encyclopedic / fiction]
- Word count: N

## Top 3 fixes
1. **[Pattern or vocabulary name]** — "exact quote from draft" → suggested rewrite
2. **[...]** — "..." → ...
3. **[...]** — "..." → ...

## Mechanical violations (from scan.py)

[Verbatim scanner output, including stats and per-category hits]

## Qualitative violations (from reading)

### Pattern violations
- **[Pattern N: name]** (severity, group): "exact quote" → fix
- **[Pattern M: name]** (severity, group): "exact quote" → fix
- ...

### Vocabulary violations
- **[Word/phrase]** (severity, ×count): "exact quote in context" → replacement
- ...

### Formatting / structural violations
- **[Tell name]** (severity): location, why it's a tell, fix
- ...

## Calibration notes

- Genre adjustment applied: [X items down-weighted because genre is academic/marketing/encyclopedic]
- Em-dash count: N (contested tell, weighted [0.5x / 1x] in this mode)
- Compound triggers: [none / one-tier escalation because three H tells in one paragraph]
- Sanded-prose signature: [present / absent — based on H-vocab clean vs structural-tells dirty]
- Uncanny-valley pattern: [present / absent — multiple weak tells stacking with low burstiness]
- Model-fingerprint markers: [list 2-3 specific phrases or structures supporting the fingerprint call, or "no clear fingerprint"]
- Contested tell notes: [any tells where research disagrees, with brief commentary]

## Recommended action

Choose one:
- **Pass — minor polish only.** No spot fixes required.
- **Spot-fix the items above.** Apply the listed corrections; the underlying voice is sound.
- **Significant cleanup needed.** Spot fixes will help but won't fully resolve the AI-shaped rhythm.
- **Recommend rewrite.** The piece has too many compounding tells; cleaner to start over.

## If revising: clean rewrite

[Full revised text — only when in fix mode. Preserves meaning, restructures rhythm, replaces flagged vocabulary, removes structural tells. The revision should be deliverable as-is.]
```

---

## Section-by-section guidance

### Verdict line

One word. The reader stops here if the verdict is `PASS` or `LOW`. The verdict tier maps directly to the density score per `calibration.md` §1:

| Verdict | Density score | What to do |
|---|---|---|
| PASS | 0–2 | Polish-pass at most |
| LOW | 2–5 | Spot-fix listed items |
| MEDIUM | 5–10 | Spot-fix sufficient; significant cleanup |
| HIGH | 10–18 | Substantial revision required |
| CRITICAL | 18+ | Recommend rewrite from scratch |

### Density score block

Always include all three counts (H/M/L) plus burstiness, model fingerprint, genre, and word count. These six lines fit on one screen and tell the reader what kind of problem they have.

If burstiness is `n/a` (fewer than 5 sentences, see `calibration.md` §8), report `n/a` rather than guessing.

If the model fingerprint is unclear, report `none`. Don't force a guess.

### Top 3 fixes

These are the highest-leverage items — the ones that, if fixed, would most reduce the verdict tier. Order by impact, not by appearance order in the draft. Each entry needs:
- The pattern or vocabulary name (so the reader can look up the full rule)
- The exact quote (so they can find it in the draft)
- A concrete rewrite (so they don't have to come up with one)

For a `PASS` audit, this section can read: "No fixes needed. The draft reads as human."

### Mechanical violations

Verbatim output from `scripts/scan.py`. Don't paraphrase — the scanner output is the receipt for the verdict. If the scanner output is long, fold it under a `<details>` HTML element so the reader can expand it on demand.

### Qualitative violations

The reading-required findings. Three subsections:
- **Pattern violations** — from `references/patterns.md`. Reference the pattern by number and group (e.g., "Pattern 13: Superficial -ing tail (B)").
- **Vocabulary violations** — from `references/vocabulary.md`. Reference the category (2A-2G) and item.
- **Formatting / structural violations** — from `references/formatting-tells.md`. Reference the section (3A-3E) and item.

Always quote the exact text from the draft. Never paraphrase the violation. The reader uses the quote to locate the issue.

### Calibration notes

This is where the audit shows its work. Without this section, the reader can't tell why the verdict is what it is. Cover:

- **Genre adjustment** — name the genre detected and what it changed
- **Em-dash count and weighting** — em dashes are contested; explicitly state the weight applied
- **Compound triggers** — note any escalation triggers from `calibration.md` §1
- **Sanded-prose signature** — present or absent, with reasoning
- **Uncanny-valley** — present or absent, with reasoning
- **Model fingerprint markers** — the 2-3 specific markers behind the fingerprint call
- **Contested tells** — any cases where research disagrees and the audit picked a side

If a calibration topic doesn't apply (no em dashes; no model fingerprint; no genre adjustment), still mention that explicitly. The reader needs to see the absence as well as the presence.

### Recommended action

One sentence. The reader uses this to decide what to do next. The four options match the verdict tiers:

- `PASS` → "Pass — minor polish only."
- `LOW` → "Spot-fix the items above."
- `MEDIUM` → "Significant cleanup needed."
- `HIGH` → "Substantial revision required."
- `CRITICAL` → "Recommend rewrite from scratch."

### If revising: clean rewrite

Only included in **fix mode** (when the user asked for polish/edit/humanize, not just audit). The rewrite:

- Preserves meaning. Don't add or remove substance.
- Replaces all H-severity violations
- Replaces M-severity violations unless the audit identified them as context-justified
- Restructures rhythm if burstiness was below 0.5
- Removes formatting tells
- Doesn't introduce new AI tells (re-scan after the rewrite if uncertain)

The rewrite should read as deliverable prose, not as a draft with edits applied.

---

## Tone and length guidance for the audit

- **Be specific.** Quote exact text. Reference exact pattern numbers.
- **Don't soften findings.** The point of the audit is to catch what the writer missed. If a draft reads heavily as AI, say so.
- **Don't pad.** A `PASS` audit can be 100 words. A `CRITICAL` audit might be 800. Match the length to the verdict.
- **Avoid AI tells in the audit itself.** The detector must not write like the thing it detects. Re-read the audit before delivery; if it contains "delve", "tapestry", grandiose framing, or sycophancy, rewrite it.

---

## Example: a minimal PASS audit

```markdown
# AI Slop Audit

## Verdict
PASS

## Density score
- High-severity tells: 0 per 500 words
- Medium-severity tells: 1 per 500 words
- Low-severity tells: 3 per 500 words (informational)
- Computed density: 0.75
- Burstiness ratio: 0.81 (humans 0.6-1.2, AI 0.2-0.4)
- Likely model fingerprint: none
- Genre detected: casual
- Word count: 487

## Top 3 fixes
No fixes needed. The draft reads as human.

## Mechanical violations
<details>
[scanner output]
</details>

## Qualitative violations
None of significance. One instance of "actually" in a context where the contrast is genuine; survives the rule.

## Calibration notes
- Genre adjustment: none (casual baseline applied)
- Em-dash count: 0
- No compound triggers
- No sanded-prose signature
- No uncanny-valley pattern
- No model fingerprint detected

## Recommended action
Pass — minor polish only.
```

## Example: a HIGH audit

The structure is the same; the populated sections are longer. See the smoke-test fixtures (a known-AI sample run through scan.py) for an example of a HIGH/CRITICAL audit with all sections populated.
