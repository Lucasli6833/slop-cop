<p align="center">
  <img src="banner.svg" alt="slop-cop catches AI prose before it ships" width="1100">
</p>

<p align="center">
  <a href="https://github.com/MahmoudHalat/slop-cop/releases/latest"><img src="https://img.shields.io/github/v/release/MahmoudHalat/slop-cop?color=ff3e9d&labelColor=0d0d0f&label=release" alt="release"></a>
  <a href="https://github.com/MahmoudHalat/slop-cop/blob/main/LICENSE"><img src="https://img.shields.io/github/license/MahmoudHalat/slop-cop?color=ff3e9d&labelColor=0d0d0f" alt="license"></a>
  <a href="#install"><img src="https://img.shields.io/badge/claude%20code-skill-7c4dff?labelColor=0d0d0f" alt="claude code skill"></a>
  <a href="#sources"><img src="https://img.shields.io/badge/sources-50%2B-ff5b3a?labelColor=0d0d0f" alt="50+ sources"></a>
  <a href="#what-it-catches"><img src="https://img.shields.io/badge/coverage-45%2B150%2B33-7c4dff?labelColor=0d0d0f" alt="coverage"></a>
</p>

---

**slop-cop** is a Claude Code skill that scans prose and tells you whether it reads as AI-shaped. Hand it a draft, get back a verdict, a density score, the exact phrases to cut, and a model fingerprint (GPT, Claude, or Gemini) when one is detectable.

It catches 45 rhetorical patterns, around 150 vocabulary tells, and around 33 formatting tells documented across peer-reviewed linguistics (PubMed, arXiv, Nature, PLOS One), Wikipedia's canonical *Signs of AI writing* guide, vendor methodology pages (GPTZero, Pangram, Originality), and the practitioner literature.

Single instances aren't a signal. Density is. slop-cop measures density, and the README you're reading passes its own test.

## Install

One command. The skill goes into your Claude Code skills directory and triggers on phrases like *"is this AI"*, *"audit this draft"*, *"humanize this"*, *"slop check"*.

```bash
curl -L https://github.com/MahmoudHalat/slop-cop/releases/latest/download/ai-slop-detector.skill -o /tmp/slop-cop.zip \
  && unzip -o /tmp/slop-cop.zip -d ~/.claude/skills/ \
  && rm /tmp/slop-cop.zip
```

That installs the bundle as `~/.claude/skills/ai-slop-detector/`. Restart Claude Code and the skill auto-loads.

Prefer git? Clone straight in:

```bash
git clone https://github.com/MahmoudHalat/slop-cop.git ~/.claude/skills/ai-slop-detector
```

## Use

In Claude Code, just talk to it:

```
audit this draft for AI tells
is this AI?
humanize this
slop-check
de-slop this paragraph
```

Or run the scanner directly:

```bash
python3 ~/.claude/skills/ai-slop-detector/scripts/scan.py path/to/draft.md
python3 ~/.claude/skills/ai-slop-detector/scripts/scan.py --quick draft.md
python3 ~/.claude/skills/ai-slop-detector/scripts/scan.py --json draft.md
python3 ~/.claude/skills/ai-slop-detector/scripts/scan.py --genre academic draft.md
python3 ~/.claude/skills/ai-slop-detector/scripts/scan.py --strict-em-dash draft.md
echo "your draft text" | python3 ~/.claude/skills/ai-slop-detector/scripts/scan.py
```

## Sample output

Two real runs from the smoke-test fixtures:

| Sample | Verdict | Density | What's flagged |
|---|---|---|---|
| Hand-written cover letter (no LLM touch) | **PASS** | 1.5 / 500w | 1 em dash, 1 intentional tricolon, 1 contextual `actually` |
| Synthetic AI marketing post | **CRITICAL** | 149.71 / 500w | `delve` (×4), `leverage` (×2), `tapestry`, sycophancy closers, vague-authority weasels, performative opener, fabricated case study, GPT fingerprint |

The scanner keeps PASSing prose that has the *texture* of human writing even when it contains a few items from the cut list. It only fires on density.

## What it catches

Three layers, each in its own reference file the scanner draws from.

| Layer | Coverage | Source |
|---|---|---|
| **Rhetorical patterns** | 45 across 5 groups: rhetorical structures, sentence-level tells, voice, decorative content, density signals | [`references/patterns.md`](ai-slop-detector/references/patterns.md) |
| **Vocabulary tells** | ~150 phrases across 7 categories: LLM-favored verbs, cliché metaphors, empty intensifiers, sycophancy, vague-authority weasels, connector clichés, academically validated spike words | [`references/vocabulary.md`](ai-slop-detector/references/vocabulary.md) |
| **Formatting tells** | ~33 across 5 categories: markdown patterns, title patterns, section organization, repetition signals, whitespace artifacts | [`references/formatting-tells.md`](ai-slop-detector/references/formatting-tells.md) |

A short list of the 20 most lethal items lives at the top of [`SKILL.md`](ai-slop-detector/SKILL.md), so the skill is useful even before any reference loads.

## Why slop-cop vs a phrase blacklist

Every "AI phrase list" you've seen has the same problem. It flags a single `delve` or one em dash and calls the prose AI. Real writing uses these words. The signal isn't presence. It's concentration.

slop-cop ships a [calibration layer](ai-slop-detector/references/calibration.md) that other detectors skip:

- **Density formula.** `(H × 3) + (M × 1) + (L × 0.25)` per 500 words. Single instances don't tip the verdict, clusters do.
- **Genre adjustment.** Academic prose can use phrases like `studies show` with citations. Marketing copy uses some intensifiers. Encyclopedic prose triggers false positives because LLMs were trained on Wikipedia. The scanner detects genre and adjusts thresholds.
- **Model fingerprint.** When AI is present, the scanner tells you which model. GPT vocabulary and Claude vocabulary diverge.
- **Sanded-prose detection.** Sophisticated authors prompt around the famous tells like `delve` and `tapestry`. The scanner weights the newer tells higher (copula avoidance, present-participle "-ing" tails, false ranges, hedge stacking) because those survive the sanding.
- **Uncanny-valley flag.** When no individual tell is severe but eight-plus weak tells stack with low burstiness, the scanner escalates anyway. That's the "subliminal discomfort" effect.
- **Burstiness measurement.** Sentence-length variance reported as a number. Humans cluster 0.6 to 1.2, LLMs cluster 0.2 to 0.4.
- **Contested-tell awareness.** Em dashes in clusters are still high signal, but isolated em dashes are now contested post-GPT-5.1 (which added an opt-out). The scanner tags both.

## Verdict scale

| Density | Verdict | Action |
|---|---|---|
| 0 to 2 | **PASS** | Polish-pass at most |
| 2 to 5 | **LOW** | Spot-fix listed items |
| 5 to 10 | **MEDIUM** | Significant cleanup |
| 10 to 18 | **HIGH** | Substantial revision |
| 18 plus | **CRITICAL** | Recommend rewrite |

Compound triggers (3+ high-severity tells in one paragraph, or the uncanny-valley pattern) escalate the verdict one tier.

## Sources

The catalog is grounded in roughly 50 published sources spanning peer-reviewed linguistics, Wikipedia's *Signs of AI writing* guide (community-maintained, model-version-aware), AI-detector vendor methodology pages, the practitioner literature (tropes.fyi, avoid-ai-writing, Pangram, Beutler Ink, Olivia Cal, GPTZero), and viral takedowns (Rolling Stone, TechRadar, LitHub, Scientific American, The Conversation, LessWrong).

Every pattern in the catalog cites the sources behind it. The full bibliography is in [`references/sources.md`](ai-slop-detector/references/sources.md).

A few highlights from the data:

- The verb `delves` rose **+6,697%** in 2024 PubMed abstracts vs 2020 ([arXiv](https://arxiv.org/html/2406.07016v1))
- `underscores` rose **+904%**, `intricate` rose **+611%** in the same window
- `today's fast-paced world` appears **107x** more in AI than human text ([GPTZero](https://gptzero.me/news/most-common-ai-vocabulary/))
- `objective study aimed` appears **269x** more in AI ([Atlas](https://www.atlas.org/blog/artificial-intelligence/top-10-cliches-in-ai-generated-text))
- A 2024 PubMed analysis estimated **at least 13.5%** of biomedical abstracts that year were processed with LLMs

## What it doesn't do

slop-cop is a detector, not a classifier. It tells you whether prose has the *shape* of AI writing (patterns, vocabulary, structure, rhythm). It doesn't tell you whether AI wrote a given piece. Skilled writers using AI as a research tool produce prose that scores PASS. Carefully prompted LLMs can produce prose that scores LOW.

Treat the verdict as *"this prose has the shape of AI writing"* rather than *"this prose was generated by AI."* The verdict is actionable. The recommendation tells you what to fix or whether to start over. The verdict is not a classification.

## Composing with other writing skills

slop-cop slots in as the final voice-check pass for any prose-producing skill (cold-email, copywriting, sales-enablement, ad-creative, email-sequence, mahmouds-seo-writer, mahmouds-reddit-strategist, mahmouds-writing-voice). When those skills are about to deliver prose, they call slop-cop in `--quick` mode and surface the verdict before handing the output back.

The `--quick` flag exists for exactly this. A one-screen output that downstream skills attach as a footer.

## License

MIT. Use it, fork it, ship a fork with a meaner verdict scale. The catalog will need updates as models change, so PRs welcome for new patterns, new spike data, and new model fingerprints.
