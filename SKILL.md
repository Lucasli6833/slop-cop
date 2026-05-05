---
name: ai-slop-detector
description: Universal AI-slop detector. Use whenever the user wants to audit, critique, score, or fix prose for AI tells (ChatGPT, Claude, Gemini, etc.). Triggers on "is this AI", "does this sound like AI", "audit for AI", "humanize this", "make this less AI", "AI slop check", "score this for AI", "detect AI writing", "slop check", "de-slop this". Also use as a final pre-delivery pass inside other writing skills (cold-email, copywriting, sales-enablement, ad-creative, email-sequence, mahmouds-seo-writer, mahmouds-reddit-strategist, mahmouds-writing-voice). Catches 45 rhetorical patterns, ~150 vocabulary tells, ~33 formatting/structural tells, with density-based scoring, genre calibration, and model fingerprinting.
---

# AI Slop Detector

A universal detector for AI-generated and AI-shaped prose. Built on ~50 published sources (peer-reviewed linguistics, Wikipedia's canonical "Signs of AI writing" guide, AI-detector vendor methodology, practitioner literature, viral takedowns) and current through early 2026.

## The one-line summary

**Single instances aren't a signal. Density is. This skill measures density.**

Every tell on every list has legitimate human use somewhere. The signal is concentration of tells per unit of text, weighted by severity, adjusted for genre and contestability. A density-aware audit catches what list-based audits miss and avoids the false positives that get flagged by list-based audits.

---

## Mode selection

Two modes. Pick one based on what the user wants.

| Signal | Mode |
|---|---|
| "audit this", "review", "critique", "what's wrong with", "is this AI", "score this", "check for AI" | **Audit** |
| "polish", "edit", "rewrite", "humanize", "make this less AI", "fix this", "de-slop", "clean up" | **Audit, then revise** (audit reveals fixes; deliver the revision) |
| User shares a draft and asks for thoughts | **Audit** (default) |
| Another writing skill is wrapping up and about to deliver prose | **Audit pass before delivery** |

If ambiguous, ask one short question: "Audit only, or do you want a revised version?" Don't ask more.

---

## When to skip

This skill governs prose meant for human readers. Skip it for:

- Code, code comments, commit messages, or PR descriptions
- Technical API documentation or reference material
- Raw data, structured outputs (JSON, YAML, CSV), or machine-readable artifacts
- Direct quotations from other people that should preserve their voice
- Instructions to other agents or skills (system prompts, agent briefs)
- Intentionally formal or legal documents that genuinely require formal register
- Dialogue under another character's voice in fiction (apply voice-aware judgment)
- Skill briefs and meta-prose written for AI consumption (this file, for example)

---

## The audit workflow

Five steps. The scanner does the mechanical work; reading does the qualitative work; calibration converts findings into a verdict.

### Step 1 — Run the scanner

```bash
python3 scripts/scan.py /path/to/draft.md
# or pipe text:
echo "draft text..." | python3 scripts/scan.py
```

Flags relevant to common cases:

```bash
# Compact one-screen output (for embedding in other skills):
python3 scripts/scan.py --quick draft.md

# Structured JSON for programmatic use:
python3 scripts/scan.py --json draft.md

# Override genre detection:
python3 scripts/scan.py --genre academic draft.md
python3 scripts/scan.py --genre marketing draft.md

# Mahmoud-mode: treat ALL em dashes as H severity
python3 scripts/scan.py --strict-em-dash draft.md
```

The scanner produces verdict, density score, burstiness, genre detection, model fingerprint, and per-category violation counts.

### Step 2 — Read against the patterns

Load `references/patterns.md` and walk through the 45 patterns by group. The scanner catches the mechanically-detectable subset; the rest requires reading. Particularly:

- **Anaphora** — the scanner finds 2-word identical openings; the qualitative version (semantic anaphora) requires reading
- **Symmetrical sentence pairs** — clause structure, not just length
- **The actual force of metaphors** — vapid vs resonant
- **"Real" tic** — when "real" survives because it's contrasting with something specific
- **"Actually"** — when it survives because it's contrasting reality with theory
- **Tone consistency** — uplift vs neutral

For each pattern, scan for instances. Flag with quote + severity.

### Step 3 — Apply calibration

Load `references/calibration.md`. Apply the following:

1. **Density-based scoring** — convert raw counts to a density score per 500 words
2. **Genre adjustment** — academic / marketing / encyclopedic / fiction get adjusted thresholds
3. **Compound triggers** — escalate the verdict when 3+ H tells in one paragraph
4. **Uncanny-valley check** — escalate when many weak tells stack with low burstiness
5. **Sanded-prose detection** — flag when famous-vocab is clean but structural tells are dirty
6. **Model fingerprint** — identify GPT vs Claude vs Gemini from marker clusters
7. **Contested tells** — em dashes, certain adverbs noted as contested

The scanner does most of this automatically. The reader applies judgment to ambiguous cases.

### Step 4 — Output the audit report

Use the format in `references/audit-report-template.md`. The report has:

- Verdict (PASS / LOW / MEDIUM / HIGH / CRITICAL)
- Density score with H/M/L counts, burstiness, model fingerprint, genre
- Top 3 fixes (highest-leverage items first)
- Mechanical violations (verbatim scanner output)
- Qualitative violations (pattern, vocabulary, formatting)
- Calibration notes (genre adjustments, contested tells, compound triggers)
- Recommended action (spot-fix / cleanup / rewrite)

Don't soften findings. The point of the audit is to catch what the writer missed.

### Step 5 — If asked, deliver the revision

If the user wanted polish/edit (not just critique), produce the full revised version after the audit. The rewrite:

- Preserves meaning. Don't add or remove substance.
- Replaces all H-severity violations
- Replaces M-severity violations unless the audit identified them as context-justified
- Restructures rhythm if burstiness was below 0.5
- Removes formatting tells
- Doesn't introduce new AI tells (re-scan after the rewrite if uncertain)

The revision should read as deliverable prose.

---

## Quick reference: the 20 most lethal tells

If you only have time to scan for one set, scan for these. Each is severity H, each is documented across multiple sources, and each appears in the highest-density AI prose. The full catalog is in `references/patterns.md` and `references/vocabulary.md`.

**Vocabulary:**
1. **delve / delves** — flagship AI verb, +6,697% in 2024 PubMed vs 2020
2. **tapestry** — iconic AI metaphor
3. **underscore / underscores** — +904% spike post-ChatGPT
4. **leverage** (as a verb) — corporate cliché
5. **harness** — rare in human prose, ubiquitous in AI

**Sentence-level patterns:**
6. **"It's not X, it's Y"** — negative parallelism / stylistic negation
7. **"serves as a..."** / **"stands as a..."** / **"boasts..."** — copula avoidance
8. **"X happened, demonstrating Y"** — present-participle "-ing" tail
9. **"From small startups to global enterprises..."** — false range
10. **"Studies show..."** with no citation — vague-authority weasel

**Voice / register:**
11. **"Great question!"** — opener sycophancy
12. **"I hope this helps!"** — closer sycophancy
13. **"In today's fast-paced world..."** — performative opener (107x more in AI)
14. **"As a society, we must..."** — royal-we framing
15. **"As of my last update..."** — knowledge-cutoff disclaimer leakage

**Structural:**
16. **"In conclusion..." / "Furthermore..." / "Moreover..."** — listicle transitions
17. **"It's worth noting that..."** — throat-clearing meta-comment
18. **Em dashes in clusters** — 3+ per 500 words (contested but still high-density signal)
19. **Bold-first bullets** (every bullet starts with **bolded keyword:**)
20. **"X: A Comprehensive Guide"** title pattern

If a draft has 5+ of these inside 500 words, the verdict is at least HIGH and the recommendation is significant rewrite.

---

## Calibration principles

A short version of the rules in `references/calibration.md`. Read the full file before producing the calibration section of the audit.

**Density formula** (per 500 words):
```
density = (H × 3) + (M × 1) + (L × 0.25)
```

**Verdict thresholds:**
- 0–2 = PASS
- 2–5 = LOW
- 5–10 = MEDIUM
- 10–18 = HIGH
- 18+ = CRITICAL

**Genre adjustments:**
- Academic prose can use "studies show" with citations and calibrated hedging
- Marketing copy tolerates more intensifiers and structural patterns
- Encyclopedic prose triggers false positives because LLMs were trained on Wikipedia
- Fiction respects character voice over the universal rules

**Contested tells:**
- Em dashes — H in clusters, L alone (Mahmoud-mode treats all as H via `--strict-em-dash`)
- "Actually" survives only contrasting reality with theory
- Tricolons in formal speeches survive

**Sanded-prose alert:**
If the famous vocabulary is clean but structural tells (copula avoidance, "-ing" tails, anaphora abuse, false ranges) are heavy, flag as "sanded prose" — the writer prompt-engineered around the v1 list but the underlying structure is still AI-shaped.

**Uncanny valley:**
If no individual tell is severe but eight or more weak tells stack with burstiness below 0.5, flag and escalate one tier. Multiple weak signals stacking causes the "subliminal discomfort" effect documented across LitHub, Pangram, and the Ignorance Field Guide.

---

## Reference loading guide

Read what the task needs.

| File | Read when |
|---|---|
| `references/patterns.md` | Always read during the qualitative pass. Full detail on the 45 rhetorical and structural patterns. |
| `references/vocabulary.md` | Read when scanning for word-level tells. ~150 items in 7 categories. |
| `references/formatting-tells.md` | Read when the draft has heavy markdown / structure. ~33 items in 5 categories. |
| `references/calibration.md` | Read at the start of every audit. Density rules, genre adjustments, model fingerprints, contested tells. |
| `references/audit-report-template.md` | Read at the start of every audit. Defines the output format. |
| `references/sources.md` | Read when challenged on a specific tell. The bibliography that backs every claim. |

The `scripts/scan.py` scanner produces a report that references the categories and items in these files.

---

## A note on the detector itself

This skill is a detector, not a classifier. It measures whether prose has the *shape* of AI writing — the patterns, vocabulary, structure, rhythm. It doesn't tell you whether AI wrote a given piece. Humans imitate AI; AI imitates humans. A skilled writer using AI as a research tool can produce prose that scores PASS. An LLM with a careful prompt can produce prose that scores LOW.

Treat the verdict as "this prose has the shape of AI writing," not "this prose was generated by AI." The verdict is actionable — the recommended action tells the writer what to fix or whether to start over. The verdict is not a classification.

The catalog will need updating as models change. After "delve" went viral in early 2024, arXiv frequency dropped sharply. After GPT-5.1 added an em-dash opt-out (Nov 2025), em-dash density became less reliable as a tell. The skill stays useful by weighting newer/less-famous patterns higher than the v1 vocabulary list, and by surfacing density rather than individual hits.

When the scanner says PASS but reading still feels wrong, trust the reading — the qualitative patterns (parallel structure, the actual force of metaphors, voice consistency) are what humans pick up on first, and what regex misses last.
