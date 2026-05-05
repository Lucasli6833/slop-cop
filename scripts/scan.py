#!/usr/bin/env python3
"""
scan.py - Universal AI-slop scanner.

Scans prose for ~45 rhetorical patterns, ~150 vocabulary tells, and ~33 formatting
tells documented in the ai-slop-detector skill. Computes density score, burstiness,
and model fingerprint. Outputs a structured audit report.

Catches what regex can; qualitative patterns (anaphora, symmetry, the actual force
of metaphors, real-vs-decorative judgment) require reading.

Usage:
    python3 scan.py path/to/draft.md
    python3 scan.py --json path/to/draft.md
    python3 scan.py --quick path/to/draft.md
    python3 scan.py --genre academic path/to/draft.md
    python3 scan.py --strict-em-dash path/to/draft.md
    cat draft.md | python3 scan.py
    echo "draft text" | python3 scan.py
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

# =============================================================================
# VOCABULARY — every item from references/vocabulary.md
# Severity: H (always cut) / M (often cut) / L (context-dependent)
# =============================================================================

# 2A. LLM-favored verbs
VERBS_H = [
    "delve into", "delves", "delved", "delve",
    "leverage", "leverages", "leveraged", "leveraging",
    "harness", "harnesses", "harnessed", "harnessing",
    "foster", "fosters", "fostered", "fostering",
    "empower", "empowers", "empowered", "empowering",
    "unlock", "unlocks", "unlocked", "unlocking",
    "elevate", "elevates", "elevated", "elevating",
    "streamline", "streamlines", "streamlined", "streamlining",
    "revolutionize", "revolutionizes", "revolutionized", "revolutionizing",
    "underscore", "underscores", "underscored", "underscoring",
    "illuminate", "illuminates", "illuminated", "illuminating",
    "navigate the", "navigates the", "navigated the", "navigating the",
    "garner", "garners", "garnered", "garnering",
    "utilize", "utilizes", "utilized", "utilizing",
    "facilitate", "facilitates", "facilitated", "facilitating",
    "embark on", "embarks on", "embarked on", "embarking on",
    "showcase", "showcases", "showcased", "showcasing",
    "boast", "boasts", "boasted", "boasting",
    "dive into", "dives into", "dove into", "diving into",
    "pave the way", "pave the way for", "paves the way",
    "shed light on", "sheds light on",
    "transform the", "transforms the", "transforming the",
]
VERBS_M = [
    "demystify", "demystifies", "demystified", "demystifying",
    "ignite", "ignites", "ignited", "igniting",
    "supercharge", "supercharges", "supercharged",
    "unleash", "unleashes", "unleashed", "unleashing",
    "unveil", "unveils", "unveiled", "unveiling",
    "resonate", "resonates", "resonated", "resonating",
    "transcend", "transcends", "transcended", "transcending",
    "spearhead", "spearheads", "spearheaded", "spearheading",
    "reimagine", "reimagines", "reimagined", "reimagining",
    "reverberate", "reverberates", "reverberated",
]

# 2B. Cliché metaphors and grandiose nouns
NOUNS_H = [
    "tapestry",
    "treasure trove",
    "symphony of",
    "embark on a journey",
    "beacon of",
    "myriad of",
    "plethora",
    "paradigm shift",
    "testament to",
    "arsenal of",
    "ecosystem of",
]
NOUNS_M = [
    "landscape of",
    "realm of",
    "journey of",
    "roadmap",
    "cornerstone of",
    "crucible",
    "labyrinth",
    "metropolis",
    "enigma",
    "kaleidoscope",
    "arena of",
]

# 2C. Empty intensifiers, hedges, vague adjectives
INTENSIFIERS_H = [
    "crucial",
    "essential",
    "vital",
    "pivotal",
    "paramount",
    "robust",
    "seamless",
    "comprehensive",
    "multifaceted",
    "intricate", "intricacies",
    "meticulous", "meticulously",
    "unwavering",
    "transformative",
    "groundbreaking",
    "cutting-edge",
    "state-of-the-art",
    "game-changer", "game-changing",
    "ever-evolving", "ever-changing",
    "fast-paced",
]
INTENSIFIERS_M = [
    "profound",
    "holistic",
    "nuanced",
    "compelling",
    "commendable",
    "insightful",
    "invaluable",
    "next-generation",
    "future-proof",
    "dynamic",
    "vibrant",
    "bustling",
    "daunting",
    "ever-expanding",
    "timeless",
    "enduring",
    "diverse array",
    "unique blend",
    "hyper-connected",
]

# 2D. Sycophantic openers / closers
SYCOPHANCY_OPEN_H = [
    r"\bGreat question[!.]",
    r"\bExcellent question[!.]",
    r"\bExcellent point[!.]",
    r"\bAbsolutely[!.]",
    r"\bCertainly[!.]",
    r"\bOf course[!.]",
    r"\bSure[!,]\s+Here'?s",
    r"\bI'?d be happy to help",
    r"\bWhat a (?:great|wonderful|fantastic) (?:question|idea)",
]
SYCOPHANCY_CLOSE_H = [
    r"\bI hope this helps",
    r"\bLet me know if you have any questions",
    r"\bLet me know if you'?d like me to (?:elaborate|continue|expand)",
    r"\bFeel free to reach out",
    r"\bDon'?t hesitate to (?:ask|reach out)",
    r"\bIs there anything else I can help you with",
    r"\bI hope this answers your question",
    r"\bHappy to clarify",
]

# 2E. Vague-authority weasel attribution
VAGUE_AUTH_H = [
    r"\bStudies show\b",
    r"\bResearch suggests\b",
    r"\bResearch indicates\b",
    r"\bMany experts (?:agree|believe)\b",
    r"\bIndustry reports indicate\b",
    r"\bIt is widely understood\b",
    r"\bIt'?s widely (?:believed|understood)\b",
    r"\bObservers have noted\b",
    r"\bSome critics argue\b",
]
VAGUE_AUTH_M = [
    r"\bGenerally speaking\b",
    r"\bIn many cases\b",
    r"\bIt is commonly (?:known|believed)\b",
]

# 2F. Closing / connector clichés
CONNECTORS_H = [
    "in conclusion",
    "to conclude",
    "in summary",
    "to summarize",
    "at the end of the day",
    "in essence",
    "to put it simply",
    "furthermore",
    "moreover",
    "additionally",
    "first and foremost",
    "last but not least",
]
CONNECTORS_M = [
    "overall",
    "ultimately",
    "all things considered",
    "in a nutshell",
    "on the other hand",
    "that being said",
    "with that in mind",
    "notably",
    "indeed",
]

# Decorative / "magic" adverbs (low+ severity)
MAGIC_ADVERBS = [
    "genuinely",
    "actually",
    "truly",
    "really",
    "honestly",
    "frankly",
    "ultimately",
    "basically",
    "obviously",
    "clearly",
    "simply",
    "literally",
    "fundamentally",
    "remarkably",
    "arguably",
    "deeply",
    "quietly",
    "subtly",
]

# Buzzwords for density check (3+ in one paragraph = flag)
BUZZWORDS = [
    "scalable",
    "repeatable",
    "defensible",
    "mission-critical",
    "enterprise-grade",
    "world-class",
    "best-in-class",
    "ai-native",
    "agent-driven",
    "autonomous",
    "high-velocity",
    "outcome-oriented",
    "robust",
    "seamless",
    "innovative",
    "cutting-edge",
    "state-of-the-art",
    "synergy",
    "holistic",
    "next-generation",
    "transformative",
    "groundbreaking",
    "comprehensive",
    "multifaceted",
]

# =============================================================================
# PATTERNS — sentence-level and structural
# =============================================================================

# 1. Negation reversal openers
NEGATION_OPENERS = [
    r"^\s*It wasn'?t\b",
    r"^\s*It was not\b",
    r"^\s*It'?s not\b",
    r"^\s*It is not\b",
    r"^\s*This isn'?t\b",
    r"^\s*This is not\b",
    r"^\s*Not just\b",
    r"^\s*Not a\b",
    r"^\s*Not because\b",
]

# 2. Dramatic countdown — "Not X. Not Y. Just Z."
# Detected via consecutive short sentences starting with "Not"

# 3. Self-posed rhetorical question + immediate answer
# "The result? X." "The catch? Y."
RHETORICAL_QA = re.compile(
    r"\b(The result|The catch|The kicker|The thing|The point|The bottom line|The real question)\?\s+\w",
    re.IGNORECASE,
)

# 8. Performative opening patterns
PERFORMATIVE_OPENINGS = [
    r"^\s*Let me cut to it[:\.]",
    r"^\s*Picture this[:\.]?",
    r"^\s*Imagine a world",
    r"^\s*In a world where",
    r"^\s*Have you ever wondered",
    r"^\s*Are you struggling with",
    r"^\s*In today'?s fast-paced",
    r"^\s*In today'?s (?:world|landscape|digital age)",
    r"^\s*Here'?s the thing\b",
    r"^\s*I'?ll be brief",
    r"^\s*When I read\b.*I closed",
    r"^\s*Most\s+\w+\s+\w+\s+(?:waste|won'?t)",
]

# 9. Setup-reveal phrases
SETUP_REVEAL_PHRASES = [
    r"\bThe point is\b",
    r"\bThe thing is\b",
    r"\bWhat this means is\b",
    r"\bIn short\b",
    r"\bBottom line\b",
    r"\bThe bottom line\b",
    r"\bIn summary\b",
    r"\bTo summarize\b",
    r"\bThe real takeaway\b",
    r"\bWhat matters here\b",
]

# 10. Crafted closer indicators
CRAFTED_CLOSERS = [
    r"^Build it\.?\s+Ship it\.?\s+Run it\.?$",
    r"^Let'?s go\.?$",
    r"^The future is now\.?$",
    r"^The future belongs to\b",
    r"^And that'?s the point\.?$",
]

# 13. Present-participle "-ing" tails
ING_TAIL = re.compile(
    r",\s+(highlighting|emphasizing|symbolizing|contributing to|reflecting|"
    r"underscoring|demonstrating|showcasing|embodying|representing|reinforcing|"
    r"signaling|illustrating|exemplifying|marking|paving|fostering)\s+",
    re.IGNORECASE,
)

# 14. False range "From X to Y"
FALSE_RANGE = re.compile(
    r"(?:^|\.\s+|:\s+)From\s+\w+(?:\s+\w+){0,3}\s+to\s+\w+(?:\s+\w+){0,3}[,.]",
    re.IGNORECASE,
)

# 15. Copula avoidance verbs
COPULA_AVOIDANCE = [
    r"\bserves as (?:a|an|the)\b",
    r"\bstands as (?:a|an|the)\b",
    r"\bmarks (?:a|an|the)\b",
    r"\brepresents (?:a|an|the)\b",
    r"\bembodies\b",
]

# 16. Hedge stacking — clusters of hedges in one sentence
HEDGE_WORDS = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bpossibly\b", r"\bpotentially\b",
    r"\bperhaps\b", r"\bgenerally\b", r"\bsomewhat\b", r"\bprobably\b",
    r"\bin many cases\b", r"\bit'?s possible that\b",
]

# 17. Hedged superlatives
HEDGED_SUPERLATIVES = [
    r"\bperhaps the most\b",
    r"\barguably the (?:best|most|greatest)\b",
    r"\bone of the most\b",
    r"\bamong the most\b",
    r"\bquite possibly the\b",
]

# 18. "While X, Y" sentence opener
WHILE_OPENER = re.compile(r"^\s*While\s+\w+", re.IGNORECASE | re.MULTILINE)

# 19. "X meets Y" / "X is more than just Y"
X_MEETS_Y = re.compile(r"\b\w+\s+meets\s+\w+\b", re.IGNORECASE)
MORE_THAN_JUST = re.compile(r"\bmore than just\s+(?:a|an)?\s*\w+", re.IGNORECASE)

# 21. False concession openers
FALSE_CONCESSION = [
    r"^\s*Despite (?:its |the |these )?(?:challenges|limitations|drawbacks)",
    r"^\s*While (?:there are|the evidence is|some)\s+\w+\s+(?:limitations|concerns|challenges)",
    r"^\s*Although (?:there are|some)\s+",
]

# 26. Pedagogical voice
PEDAGOGICAL = [
    r"^\s*Let'?s dive into\b",
    r"^\s*Let'?s explore\b",
    r"^\s*Let'?s break (?:this|it) down\b",
    r"^\s*We'?ll walk through\b",
    r"^\s*Let'?s unpack\b",
]

# 27. Royal-we / "as a society" framing
ROYAL_WE = [
    r"\bWe live in (?:an? |the )?(?:age|era|world)\b",
    r"\bAs a society,? we\b",
    r"\bIn our (?:time|age|world)\b",
    r"\bOur collective\b",
]

# 29. Knowledge-cutoff disclaimer leakage
KNOWLEDGE_CUTOFF = [
    r"\bAs of my (?:last update|knowledge cutoff)\b",
    r"\bI don'?t have access to real-time\b",
    r"\bMy training data\b",
    r"\bWhile my training\b",
    r"\bbased on (?:my|the) training data\b",
]

# 31. Stake inflation / future-flourish
STAKE_INFLATION = [
    r"\bThis will revolutionize\b",
    r"\bWe'?re entering (?:a|the) new era\b",
    r"\bA new paradigm\b",
    r"\bThe future of\b.*\bis\b",
    r"\bUshering in (?:a|the) new\b",
]

# 32. Grandiose framing
GRANDIOSE = [
    r"\bstands as (?:a|an|the)\b",
    r"\bserves as (?:a|an|the)\b",
    r"\b(?:a|the) testament to\b",
    r"\bAt its core,?\s+(?:this|the|it)\b",
    r"\bembodies (?:the|a) spirit\b",
    r"\brepresents (?:a|an|the)\s+\w+\s+(?:moment|era|chapter)",
]

# 36. Fabricated case study / generic name
FABRICATED_CASE = re.compile(
    r"\b(?:Take|Meet|Consider)\s+([A-Z][a-z]{2,10})(?:\s+[A-Z][a-z]+)?,\s+(?:a|an)\s+",
)

# 41. Throat-clearing meta-comments
THROAT_CLEARING = [
    r"\bIt'?s worth noting (?:that)?\b",
    r"\bIt'?s important to (?:mention|note)\b",
    r"\bIt bears (?:mentioning|noting)\b",
    r"^\s*Notably,\s",
    r"^\s*Interestingly,\s",
]

# Whether-or openers (12)
WHETHER_OR = re.compile(r"^\s*Whether you'?re\s+", re.IGNORECASE | re.MULTILINE)

# =============================================================================
# MODEL FINGERPRINT MARKERS
# =============================================================================

GPT_MARKERS = [
    r"\bdelve(?:s|d)?\b", r"\bunderscore(?:s|d)?\b", r"\bnoteworthy\b",
    r"\bcommendable\b", r"\bintricate\b", r"\bmeticulous(?:ly)?\b",
    r"\bsupercharge\b", r"\bunleash(?:es|ed)?\b", r"\bdive in\b",
    r"\bgame-changing\b", r"\bindividuals with\b",
    r"\bcharacterized by elevated\b", r"\bplay a significant role\b",
]
CLAUDE_MARKERS = [
    r"\bmeaningfully\b", r"\bthe distinction is worth examining\b",
    r"\bI notice that\b", r"\bit'?s worth examining\b",
    r"\bI should be careful here\b", r"\bworth noting that\b",
    r"\bmore carefully\b",
]
GEMINI_MARKERS = [
    r"\bthe way for\b", r"\bthe cascade of\b", r"\bin the world of\b",
    r"\blet'?s explore\b", r"\bunderstand how\b",
    r"\blet'?s take a closer look\b",
]

# =============================================================================
# TEXT PROCESSING
# =============================================================================

ABBREVIATIONS = [
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.",
    "U.S.", "U.K.", "E.U.", "i.e.", "e.g.", "etc.", "vs.", "Inc.", "Ltd.",
    "St.", "Ave.", "No.", "Vol.", "ch.", "ed.",
]


def strip_code_blocks(text):
    """Remove fenced code blocks and inline code from markdown."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    return text


def split_sentences(text):
    """Split text into sentences. Imperfect but good enough."""
    protected = text
    for ab in ABBREVIATIONS:
        protected = protected.replace(ab, ab.replace(".", "\x00"))
    sentences = re.split(r"(?<=[.!?])\s+", protected)
    sentences = [s.replace("\x00", ".").strip() for s in sentences if s.strip()]
    return sentences


def split_paragraphs(text):
    """Split text into paragraphs by blank lines."""
    paras = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paras if p.strip()]


def count_words(s):
    return len(re.findall(r"\b\w+\b", s))


def find_phrase_hits(text, phrases):
    """Return [(phrase, count), ...] for whole-word phrases (case-insensitive)."""
    hits = []
    for phrase in phrases:
        # Word boundaries around the phrase
        pattern = r"\b" + re.escape(phrase) + r"\b"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            hits.append((phrase, len(matches)))
    return hits


def find_regex_hits(text, patterns):
    """Return [(pattern, count, sample), ...] for each pattern with matches."""
    hits = []
    for pat in patterns:
        matches = re.findall(pat, text, flags=re.IGNORECASE)
        if matches:
            sample = matches[0] if isinstance(matches[0], str) else str(matches[0])
            hits.append((pat, len(matches), sample[:80]))
    return hits


# =============================================================================
# DETECTORS
# =============================================================================

def find_em_dashes(text):
    em = text.count("—")
    en = text.count("–")
    double_hyphen = len(re.findall(r"(?<!-)--(?!-)", text))
    return em, en, double_hyphen


def find_short_sentence_clusters(sentences, threshold=8, min_run=3):
    """Find runs of consecutive short sentences."""
    runs = []
    current = []
    for i, s in enumerate(sentences):
        wc = count_words(s)
        if wc <= threshold:
            current.append((i, s, wc))
        else:
            if len(current) >= min_run:
                runs.append(list(current))
            current = []
    if len(current) >= min_run:
        runs.append(list(current))
    return runs


def find_two_word_punchlines(sentences, short_max=4, long_min=20):
    """Find any sentence ≤short_max words preceded by one ≥long_min words."""
    hits = []
    for i in range(1, len(sentences)):
        prev_wc = count_words(sentences[i - 1])
        cur_wc = count_words(sentences[i])
        if prev_wc >= long_min and cur_wc <= short_max:
            hits.append((i, sentences[i], cur_wc, sentences[i - 1][:80]))
    return hits


def find_negation_reversal_candidates(sentences):
    hits = []
    for i, s in enumerate(sentences):
        for pat in NEGATION_OPENERS:
            if re.search(pat, s):
                hits.append((i, s, pat))
                break
    return hits


def find_dramatic_countdown(sentences):
    """Find 2+ consecutive short sentences starting with 'Not'."""
    hits = []
    for i in range(1, len(sentences)):
        prev = sentences[i - 1]
        cur = sentences[i]
        if (
            count_words(prev) <= 8
            and count_words(cur) <= 8
            and re.match(r"^\s*Not\b", prev, re.IGNORECASE)
            and re.match(r"^\s*Not\b", cur, re.IGNORECASE)
        ):
            hits.append((i, [prev, cur]))
    return hits


def find_anaphora(sentences, min_run=3):
    """3+ consecutive sentences starting with the same 2-word opening."""
    hits = []
    if len(sentences) < min_run:
        return hits
    current_run = [0]
    for i in range(1, len(sentences)):
        prev_words = sentences[i - 1].split()[:2]
        cur_words = sentences[i].split()[:2]
        if (
            len(prev_words) == 2 and len(cur_words) == 2
            and prev_words[0].lower() == cur_words[0].lower()
            and prev_words[1].lower() == cur_words[1].lower()
        ):
            current_run.append(i)
        else:
            if len(current_run) >= min_run:
                hits.append([(idx, sentences[idx]) for idx in current_run])
            current_run = [i]
    if len(current_run) >= min_run:
        hits.append([(idx, sentences[idx]) for idx in current_run])
    return hits


def find_three_beat_stacks(text):
    """Heuristic: 'word, word, and word' pattern."""
    pattern = r"\b(\w+(?:\s+\w+)?)\s*,\s*(\w+(?:\s+\w+)?)\s*,\s*and\s+(\w+(?:\s+\w+)?)\b"
    return re.findall(pattern, text)


def find_setup_reveal_endings(paragraphs):
    """Paragraphs ending with a setup-reveal phrase."""
    hits = []
    for i, p in enumerate(paragraphs):
        sentences = split_sentences(p)
        if not sentences:
            continue
        last = sentences[-1]
        for pat in SETUP_REVEAL_PHRASES:
            if re.search(pat, last, flags=re.IGNORECASE):
                hits.append((i, last, pat))
                break
    return hits


def find_buzzword_density(paragraphs, threshold=3):
    """Paragraphs with `threshold`+ buzzwords."""
    hits = []
    for i, p in enumerate(paragraphs):
        count = 0
        found = []
        for bw in BUZZWORDS:
            pattern = r"\b" + re.escape(bw) + r"\b"
            n = len(re.findall(pattern, p, flags=re.IGNORECASE))
            if n:
                count += n
                found.append((bw, n))
        if count >= threshold:
            hits.append((i, count, found))
    return hits


def find_crafted_closer(text):
    """Final non-empty line matches crafted-closer patterns."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return None
    last = lines[-1]
    for pat in CRAFTED_CLOSERS:
        if re.search(pat, last, flags=re.IGNORECASE):
            return (last, pat)
    return None


def find_performative_opening(text):
    """First sentence matches a performative opening pattern."""
    sentences = split_sentences(strip_code_blocks(text))
    if not sentences:
        return None
    first = sentences[0]
    for pat in PERFORMATIVE_OPENINGS:
        if re.search(pat, first, flags=re.IGNORECASE):
            return (first, pat)
    return None


def find_hedge_stacking(sentences):
    """Sentences with 3+ hedge words."""
    hits = []
    for i, s in enumerate(sentences):
        count = 0
        for pat in HEDGE_WORDS:
            count += len(re.findall(pat, s, flags=re.IGNORECASE))
        if count >= 3:
            hits.append((i, s, count))
    return hits


def find_while_openers(text):
    """Count 'While X, Y' sentence openers."""
    matches = WHILE_OPENER.findall(text)
    return len(matches)


def find_acknowledgment_loop(text, title=None):
    """First sentence echoes the title (if provided) or paraphrases prompt."""
    if not title:
        return None
    sentences = split_sentences(strip_code_blocks(text))
    if not sentences:
        return None
    first = sentences[0].lower()
    title_words = set(re.findall(r"\b\w+\b", title.lower()))
    first_words = set(re.findall(r"\b\w+\b", first))
    overlap = title_words & first_words
    # Stop words don't count
    stop = {"a", "an", "the", "to", "of", "in", "on", "for", "and", "or", "is", "are"}
    overlap -= stop
    if len(overlap) >= 3:
        return (first, list(overlap))
    return None


def find_fabricated_cases(text):
    """Find 'Take Sarah, a marketing manager...' patterns."""
    return FABRICATED_CASE.findall(text)


def compute_burstiness(sentences):
    """Std dev of sentence lengths divided by mean. Returns None for <5 sentences."""
    if len(sentences) < 5:
        return None
    lengths = [count_words(s) for s in sentences]
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return None
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    std = math.sqrt(variance)
    return round(std / mean, 3)


def find_bigram_repetition(text, threshold=5):
    """Find 2-word phrases appearing `threshold`+ times. Excludes stopword-only bigrams."""
    words = re.findall(r"\b\w+\b", text.lower())
    if len(words) < 10:
        return []
    bigrams = {}
    stop = {"a", "an", "the", "to", "of", "in", "on", "for", "and", "or", "is", "are",
            "be", "was", "were", "by", "as", "at", "with", "this", "that", "it", "its"}
    for i in range(len(words) - 1):
        if words[i] in stop and words[i + 1] in stop:
            continue
        bg = (words[i], words[i + 1])
        bigrams[bg] = bigrams.get(bg, 0) + 1
    return [(bg, count) for bg, count in bigrams.items() if count >= threshold]


def contraction_ratio(text):
    """Ratio of contractions to could-be-contractions. 0 = formal/AI lean."""
    contractions = len(re.findall(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", text))
    expansions = len(re.findall(r"\b(?:do not|does not|did not|will not|would not|could not|should not|cannot|can not|is not|are not|was not|were not|has not|have not|had not|it is|that is|there is|i am)\b", text, flags=re.IGNORECASE))
    total = contractions + expansions
    if total == 0:
        return None
    return round(contractions / total, 2)


def detect_model_fingerprint(text):
    """Heuristic: count GPT/Claude/Gemini markers and report dominant."""
    gpt_count = sum(len(re.findall(p, text, flags=re.IGNORECASE)) for p in GPT_MARKERS)
    claude_count = sum(len(re.findall(p, text, flags=re.IGNORECASE)) for p in CLAUDE_MARKERS)
    gemini_count = sum(len(re.findall(p, text, flags=re.IGNORECASE)) for p in GEMINI_MARKERS)

    total = gpt_count + claude_count + gemini_count
    if total < 2:
        return ("none", {"gpt": gpt_count, "claude": claude_count, "gemini": gemini_count})

    # Find max
    counts = {"gpt": gpt_count, "claude": claude_count, "gemini": gemini_count}
    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])
    if sorted_counts[0][1] >= 2 and sorted_counts[0][1] >= 1.5 * (sorted_counts[1][1] or 1):
        return (sorted_counts[0][0], counts)
    return ("mixed", counts)


def detect_genre(text):
    """Crude genre inference. Falls back to 'casual'."""
    text_lower = text.lower()
    # Academic markers
    if (
        len(re.findall(r"\b(?:hypothesis|methodology|et al\.|fig\.|p\s*<\s*0\.0|table \d+)", text_lower)) >= 2
        or "abstract:" in text_lower
        or re.search(r"\[\d+\]|\(\d{4}\)", text)
    ):
        return "academic"
    # Marketing markers
    if len(re.findall(r"\b(?:cta|conversion|landing page|sign up|free trial|book a demo|pricing)\b", text_lower)) >= 2:
        return "marketing"
    # Encyclopedic markers
    if (
        re.search(r"^[A-Z][\w\s]+ \(born", text)
        or re.search(r"^[A-Z][\w\s]+ \(c\.\s*\d{4}", text)
        or len(re.findall(r"\bwas (?:a|an|the)\b", text)) >= 5
    ):
        return "encyclopedic"
    # Fiction: dialogue heavy
    if text.count('"') >= 6:
        return "fiction"
    return "casual"


def find_markdown_tells(text):
    """Detect bold-first bullets, emoji bullets, excessive headers, etc."""
    tells = {}
    # Bold-first bullets
    bold_bullets = len(re.findall(r"^\s*[-*]\s+\*\*[^*]+\*\*\s*[:.]", text, flags=re.MULTILINE))
    if bold_bullets >= 3:
        tells["bold_first_bullets"] = bold_bullets
    # Emoji bullets
    emoji_bullets = len(re.findall(r"^\s*[🔹✨📌📍🎯💡⭐🚀🔥]", text, flags=re.MULTILINE))
    if emoji_bullets >= 1:
        tells["emoji_bullets"] = emoji_bullets
    # Excessive headers
    h2_count = len(re.findall(r"^##\s+", text, flags=re.MULTILINE))
    h3_count = len(re.findall(r"^###\s+", text, flags=re.MULTILINE))
    word_count = count_words(text)
    if word_count > 0 and (h2_count + h3_count) > word_count / 200:
        tells["excessive_headers"] = {
            "h2": h2_count, "h3": h3_count, "word_count": word_count,
        }
    # Title patterns in headers
    title_patterns = re.findall(
        r"^#+\s+(?:[\w\s]+:\s+(?:A|The|Your|Everything)\s+(?:Comprehensive|Ultimate|Definitive|Complete)\s+Guide|The Ultimate Guide to|Everything You Need to Know|How to \w+ in 20\d{2})",
        text, flags=re.MULTILINE | re.IGNORECASE,
    )
    if title_patterns:
        tells["clichéd_title_patterns"] = title_patterns
    return tells


# =============================================================================
# ANALYSIS
# =============================================================================

def analyze(text, genre=None, strict_em_dash=False):
    """Run the full scan and return a structured result."""
    clean = strip_code_blocks(text)
    paragraphs = split_paragraphs(clean)
    sentences = split_sentences(clean)
    word_counts = [count_words(s) for s in sentences]
    total_words = sum(word_counts)

    em, en, dh = find_em_dashes(text)

    # Genre detection
    detected_genre = detect_genre(clean)
    if not genre:
        genre = detected_genre

    # Model fingerprint
    fingerprint, fp_counts = detect_model_fingerprint(clean)

    # Burstiness
    burst = compute_burstiness(sentences)

    # Build results
    result = {
        "stats": {
            "words": total_words,
            "paragraphs": len(paragraphs),
            "sentences": len(sentences),
            "sentence_avg": round(sum(word_counts) / len(word_counts), 1) if word_counts else 0,
            "sentence_min": min(word_counts) if word_counts else 0,
            "sentence_max": max(word_counts) if word_counts else 0,
            "burstiness": burst,
            "contraction_ratio": contraction_ratio(clean),
            "detected_genre": detected_genre,
            "applied_genre": genre,
            "model_fingerprint": fingerprint,
            "fingerprint_counts": fp_counts,
        },
        "high": {
            "em_dashes": em,
            "en_dashes": en,
            "double_hyphens": dh,
            "verbs_h": find_phrase_hits(clean, VERBS_H),
            "nouns_h": find_phrase_hits(clean, NOUNS_H),
            "intensifiers_h": find_phrase_hits(clean, INTENSIFIERS_H),
            "connectors_h": find_phrase_hits(clean, CONNECTORS_H),
            "sycophancy_open": find_regex_hits(clean, SYCOPHANCY_OPEN_H),
            "sycophancy_close": find_regex_hits(clean, SYCOPHANCY_CLOSE_H),
            "vague_authority_h": find_regex_hits(clean, VAGUE_AUTH_H),
            "knowledge_cutoff": find_regex_hits(clean, KNOWLEDGE_CUTOFF),
            "stake_inflation": find_regex_hits(clean, STAKE_INFLATION),
            "grandiose": find_regex_hits(clean, GRANDIOSE),
            "copula_avoidance": find_regex_hits(clean, COPULA_AVOIDANCE),
            "ing_tails": ING_TAIL.findall(clean),
            "throat_clearing": find_regex_hits(clean, THROAT_CLEARING),
            "rhetorical_qa": RHETORICAL_QA.findall(clean),
            "crafted_closer": find_crafted_closer(clean),
            "performative_opening": find_performative_opening(clean),
            "setup_reveal_endings": find_setup_reveal_endings(paragraphs),
            "fabricated_cases": find_fabricated_cases(clean),
            "buzzword_density": find_buzzword_density(paragraphs),
        },
        "medium": {
            "negation_reversals": find_negation_reversal_candidates(sentences),
            "dramatic_countdown": find_dramatic_countdown(sentences),
            "anaphora": find_anaphora(sentences),
            "two_word_punchlines": find_two_word_punchlines(sentences),
            "three_beat_stacks": find_three_beat_stacks(clean),
            "verbs_m": find_phrase_hits(clean, VERBS_M),
            "nouns_m": find_phrase_hits(clean, NOUNS_M),
            "intensifiers_m": find_phrase_hits(clean, INTENSIFIERS_M),
            "connectors_m": find_phrase_hits(clean, CONNECTORS_M),
            "vague_authority_m": find_regex_hits(clean, VAGUE_AUTH_M),
            "hedge_stacking": find_hedge_stacking(sentences),
            "hedged_superlatives": find_regex_hits(clean, HEDGED_SUPERLATIVES),
            "while_openers": find_while_openers(clean),
            "x_meets_y": len(X_MEETS_Y.findall(clean)),
            "more_than_just": len(MORE_THAN_JUST.findall(clean)),
            "false_concession": find_regex_hits(clean, FALSE_CONCESSION),
            "false_range": len(FALSE_RANGE.findall(clean)),
            "pedagogical": find_regex_hits(clean, PEDAGOGICAL),
            "royal_we": find_regex_hits(clean, ROYAL_WE),
            "whether_or_openers": len(WHETHER_OR.findall(clean)),
        },
        "low": {
            "magic_adverbs": find_phrase_hits(clean, MAGIC_ADVERBS),
            "short_sentence_clusters": find_short_sentence_clusters(sentences),
            "bigram_repetition": find_bigram_repetition(clean),
            "markdown_tells": find_markdown_tells(text),
        },
    }

    # Compute counts
    high_count = (
        result["high"]["em_dashes"]
        + result["high"]["en_dashes"]
        + result["high"]["double_hyphens"]
        + sum(c for _, c in result["high"]["verbs_h"])
        + sum(c for _, c in result["high"]["nouns_h"])
        + sum(c for _, c in result["high"]["intensifiers_h"])
        + sum(c for _, c in result["high"]["connectors_h"])
        + sum(c for _, _, c in [])  # placeholder
        + sum(c for _, c, _ in result["high"]["sycophancy_open"])
        + sum(c for _, c, _ in result["high"]["sycophancy_close"])
        + sum(c for _, c, _ in result["high"]["vague_authority_h"])
        + sum(c for _, c, _ in result["high"]["knowledge_cutoff"])
        + sum(c for _, c, _ in result["high"]["stake_inflation"])
        + sum(c for _, c, _ in result["high"]["grandiose"])
        + sum(c for _, c, _ in result["high"]["copula_avoidance"])
        + len(result["high"]["ing_tails"])
        + sum(c for _, c, _ in result["high"]["throat_clearing"])
        + len(result["high"]["rhetorical_qa"])
        + (1 if result["high"]["crafted_closer"] else 0)
        + (1 if result["high"]["performative_opening"] else 0)
        + len(result["high"]["setup_reveal_endings"])
        + len(result["high"]["fabricated_cases"])
        + len(result["high"]["buzzword_density"])
    )
    medium_count = (
        len(result["medium"]["negation_reversals"])
        + len(result["medium"]["dramatic_countdown"])
        + len(result["medium"]["anaphora"])
        + len(result["medium"]["two_word_punchlines"])
        + len(result["medium"]["three_beat_stacks"])
        + sum(c for _, c in result["medium"]["verbs_m"])
        + sum(c for _, c in result["medium"]["nouns_m"])
        + sum(c for _, c in result["medium"]["intensifiers_m"])
        + sum(c for _, c in result["medium"]["connectors_m"])
        + sum(c for _, c, _ in result["medium"]["vague_authority_m"])
        + len(result["medium"]["hedge_stacking"])
        + sum(c for _, c, _ in result["medium"]["hedged_superlatives"])
        + result["medium"]["while_openers"]
        + result["medium"]["x_meets_y"]
        + result["medium"]["more_than_just"]
        + sum(c for _, c, _ in result["medium"]["false_concession"])
        + result["medium"]["false_range"]
        + sum(c for _, c, _ in result["medium"]["pedagogical"])
        + sum(c for _, c, _ in result["medium"]["royal_we"])
        + result["medium"]["whether_or_openers"]
    )
    low_count = (
        sum(c for _, c in result["low"]["magic_adverbs"])
        + len(result["low"]["short_sentence_clusters"])
        + len(result["low"]["bigram_repetition"])
        + len(result["low"]["markdown_tells"])
    )

    # Apply genre adjustments
    if genre == "marketing":
        # Marketing legitimately uses some intensifiers and structure
        # Down-weight intensifier and connector buzzwords slightly
        adjusted_h = high_count - int(0.3 * sum(c for _, c in result["high"]["intensifiers_h"]))
        adjusted_h = max(0, adjusted_h)
        high_count = adjusted_h
    elif genre == "academic":
        # Academic legitimately uses hedging
        adjusted_m = medium_count - len(result["medium"]["hedge_stacking"])
        adjusted_m = max(0, adjusted_m)
        medium_count = adjusted_m
    elif genre == "encyclopedic":
        # Wikipedia-style triggers false positives — reduce all by one tier
        high_count = max(0, high_count - 2)
        medium_count = max(0, medium_count - 2)

    # Em-dash strict mode
    if strict_em_dash and em > 0:
        # Already counted as H; nothing extra needed
        pass
    elif not strict_em_dash:
        # Em dashes alone = L unless 3+ per 500 words
        if total_words > 0 and em < (3 * total_words / 500):
            # Move em dashes from high to low
            high_count -= em
            low_count += em

    # Compute density score per calibration.md §1
    units = max(1, total_words / 500)
    density = ((high_count * 3) + (medium_count * 1) + (low_count * 0.25)) / units

    # Verdict thresholds
    if density >= 18:
        verdict = "CRITICAL"
    elif density >= 10:
        verdict = "HIGH"
    elif density >= 5:
        verdict = "MEDIUM"
    elif density >= 2:
        verdict = "LOW"
    else:
        verdict = "PASS"

    # Compound triggers
    escalated = False
    # Three or more H tells in one paragraph
    paragraphs_with_h = []
    for p in paragraphs:
        h_in_p = 0
        for phrases in [VERBS_H, NOUNS_H, INTENSIFIERS_H, CONNECTORS_H]:
            for ph in phrases:
                h_in_p += len(re.findall(r"\b" + re.escape(ph) + r"\b", p, flags=re.IGNORECASE))
        if h_in_p >= 3:
            paragraphs_with_h.append((p[:80], h_in_p))
    if paragraphs_with_h:
        escalated = True

    # Uncanny valley
    uncanny_valley = False
    if (
        high_count == 0
        and (medium_count + low_count) >= 8 * units
        and burst is not None and burst < 0.5
    ):
        uncanny_valley = True
        escalated = True

    if escalated:
        verdict_order = ["PASS", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        idx = verdict_order.index(verdict)
        verdict = verdict_order[min(len(verdict_order) - 1, idx + 1)]

    # Sanded-prose signature
    h_vocab_total = (
        sum(c for _, c in result["high"]["verbs_h"])
        + sum(c for _, c in result["high"]["nouns_h"])
    )
    structural_count = (
        sum(c for _, c, _ in result["high"]["copula_avoidance"])
        + len(result["high"]["ing_tails"])
        + len(result["medium"]["negation_reversals"])
        + len(result["medium"]["anaphora"])
        + result["medium"]["false_range"]
        + result["medium"]["while_openers"]
        + len(result["medium"]["hedge_stacking"])
    )
    sanded = h_vocab_total <= 1 and structural_count >= 5

    result["verdict"] = verdict
    result["totals"] = {"high": high_count, "medium": medium_count, "low": low_count}
    result["density"] = round(density, 2)
    result["calibration"] = {
        "compound_escalation": bool(paragraphs_with_h),
        "uncanny_valley": uncanny_valley,
        "sanded_prose": sanded,
        "em_dash_mode": "strict" if strict_em_dash else "default",
    }
    return result


# =============================================================================
# OUTPUT FORMATTERS
# =============================================================================

def format_human(result):
    lines = []
    s = result["stats"]
    lines.append("=" * 70)
    lines.append("AI SLOP SCAN REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Verdict:           {result['verdict']}")
    lines.append(f"Density score:     {result['density']} per 500w")
    lines.append(
        f"Violations:        {result['totals']['high']}H, "
        f"{result['totals']['medium']}M, {result['totals']['low']}L"
    )
    lines.append("")
    lines.append("--- Stats ---")
    lines.append(f"Words: {s['words']} | Paragraphs: {s['paragraphs']} | Sentences: {s['sentences']}")
    lines.append(f"Sentence avg: {s['sentence_avg']}w | min {s['sentence_min']}w | max {s['sentence_max']}w")
    burst = s["burstiness"]
    burst_str = f"{burst} (humans 0.6-1.2, AI 0.2-0.4)" if burst is not None else "n/a (too few sentences)"
    lines.append(f"Burstiness:        {burst_str}")
    contr = s["contraction_ratio"]
    lines.append(f"Contraction ratio: {contr if contr is not None else 'n/a'}")
    lines.append(f"Detected genre:    {s['detected_genre']}")
    if s["applied_genre"] != s["detected_genre"]:
        lines.append(f"Applied genre:     {s['applied_genre']} (override)")
    lines.append(f"Model fingerprint: {s['model_fingerprint']} {s['fingerprint_counts']}")
    lines.append("")

    # Calibration
    cal = result["calibration"]
    lines.append("--- Calibration ---")
    if cal["compound_escalation"]:
        lines.append("COMPOUND TRIGGER: 3+ H tells in one paragraph — verdict escalated one tier")
    if cal["uncanny_valley"]:
        lines.append("UNCANNY VALLEY: many weak tells stacking with low burstiness")
    if cal["sanded_prose"]:
        lines.append("SANDED-PROSE SIGNATURE: low famous-vocab, high structural — looks prompt-engineered")
    lines.append(f"Em-dash mode: {cal['em_dash_mode']}")
    lines.append("")

    # High severity
    h = result["high"]
    lines.append("--- HIGH SEVERITY ---")
    if h["em_dashes"] or h["en_dashes"] or h["double_hyphens"]:
        lines.append(f"Em/en dashes / double-hyphens: {h['em_dashes']}/{h['en_dashes']}/{h['double_hyphens']}")
    if h["verbs_h"]:
        lines.append("LLM-favored verbs:")
        for phrase, count in h["verbs_h"]:
            lines.append(f"  - \"{phrase}\" ×{count}")
    if h["nouns_h"]:
        lines.append("Cliché metaphors / grandiose nouns:")
        for phrase, count in h["nouns_h"]:
            lines.append(f"  - \"{phrase}\" ×{count}")
    if h["intensifiers_h"]:
        lines.append("Empty intensifiers:")
        for phrase, count in h["intensifiers_h"]:
            lines.append(f"  - \"{phrase}\" ×{count}")
    if h["connectors_h"]:
        lines.append("Closing/connector clichés:")
        for phrase, count in h["connectors_h"]:
            lines.append(f"  - \"{phrase}\" ×{count}")
    if h["sycophancy_open"]:
        lines.append("Sycophancy openers:")
        for pat, count, sample in h["sycophancy_open"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if h["sycophancy_close"]:
        lines.append("Sycophancy closers:")
        for pat, count, sample in h["sycophancy_close"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if h["vague_authority_h"]:
        lines.append("Vague-authority weasels:")
        for pat, count, sample in h["vague_authority_h"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if h["knowledge_cutoff"]:
        lines.append("Knowledge-cutoff disclaimer leakage:")
        for pat, count, sample in h["knowledge_cutoff"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if h["stake_inflation"]:
        lines.append("Stake inflation / future-flourish:")
        for pat, count, sample in h["stake_inflation"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if h["grandiose"]:
        lines.append("Grandiose framing:")
        for pat, count, sample in h["grandiose"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if h["copula_avoidance"]:
        lines.append("Copula avoidance:")
        for pat, count, sample in h["copula_avoidance"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if h["ing_tails"]:
        lines.append(f"Present-participle '-ing' tails: {len(h['ing_tails'])}")
        for t in h["ing_tails"][:5]:
            lines.append(f"  - \"...{t}...\"")
    if h["throat_clearing"]:
        lines.append("Throat-clearing meta-comments:")
        for pat, count, sample in h["throat_clearing"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if h["rhetorical_qa"]:
        lines.append(f"Self-posed rhetorical Q+A: {len(h['rhetorical_qa'])}")
    if h["performative_opening"]:
        lines.append(f"Performative opening: \"{h['performative_opening'][0][:80]}\"")
    if h["crafted_closer"]:
        lines.append(f"Crafted closer: \"{h['crafted_closer'][0]}\"")
    if h["setup_reveal_endings"]:
        lines.append("Setup-reveal endings:")
        for idx, sentence, pat in h["setup_reveal_endings"]:
            lines.append(f"  - Para {idx+1}: \"{sentence[:120]}\"")
    if h["fabricated_cases"]:
        lines.append(f"Fabricated case studies: {h['fabricated_cases']}")
    if h["buzzword_density"]:
        lines.append("Buzzword density (3+ in one paragraph):")
        for idx, count, found in h["buzzword_density"]:
            words = ", ".join(f"{w}×{n}" for w, n in found)
            lines.append(f"  - Para {idx+1}: {count} buzzwords ({words})")
    lines.append("")

    # Medium severity
    m = result["medium"]
    lines.append("--- MEDIUM SEVERITY ---")
    if m["negation_reversals"]:
        lines.append("Negation reversal candidates:")
        for idx, sentence, pat in m["negation_reversals"]:
            lines.append(f"  - Sentence {idx+1}: \"{sentence[:120]}\"")
    if m["dramatic_countdown"]:
        lines.append("Dramatic countdown candidates:")
        for idx, sents in m["dramatic_countdown"]:
            for s in sents:
                lines.append(f"  - \"{s[:80]}\"")
    if m["anaphora"]:
        lines.append("Anaphora abuse (3+ identical openings):")
        for run in m["anaphora"]:
            lines.append(f"  - {len(run)} consecutive sentences:")
            for idx, sent in run:
                lines.append(f"    \"{sent[:80]}\"")
    if m["two_word_punchlines"]:
        lines.append("Two-word punchline candidates:")
        for idx, sentence, wc, prev in m["two_word_punchlines"]:
            lines.append(f"  - Sentence {idx+1} ({wc}w): \"{sentence}\" after \"{prev}...\"")
    if m["three_beat_stacks"]:
        lines.append(f"Three-beat stack candidates: {len(m['three_beat_stacks'])}")
        for triple in m["three_beat_stacks"][:5]:
            lines.append(f"  - \"{triple[0]}, {triple[1]}, and {triple[2]}\"")
    for label, items in [
        ("LLM-favored verbs (M)", m["verbs_m"]),
        ("Cliché metaphors (M)", m["nouns_m"]),
        ("Empty intensifiers (M)", m["intensifiers_m"]),
        ("Connectors (M)", m["connectors_m"]),
    ]:
        if items:
            lines.append(f"{label}:")
            for phrase, count in items:
                lines.append(f"  - \"{phrase}\" ×{count}")
    if m["hedge_stacking"]:
        lines.append(f"Hedge stacking (3+ hedges in one sentence): {len(m['hedge_stacking'])}")
        for idx, sent, count in m["hedge_stacking"][:3]:
            lines.append(f"  - {count} hedges: \"{sent[:120]}\"")
    if m["hedged_superlatives"]:
        lines.append("Hedged superlatives:")
        for pat, count, sample in m["hedged_superlatives"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if m["while_openers"] >= 2:
        lines.append(f"'While X, Y' openers: {m['while_openers']} (pattern emerges at >2)")
    if m["x_meets_y"]:
        lines.append(f"'X meets Y' formula: {m['x_meets_y']}")
    if m["more_than_just"]:
        lines.append(f"'More than just X' formula: {m['more_than_just']}")
    if m["false_range"]:
        lines.append(f"False range ('From X to Y'): {m['false_range']}")
    if m["false_concession"]:
        lines.append("False concession openers:")
        for pat, count, sample in m["false_concession"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if m["pedagogical"]:
        lines.append("Pedagogical voice:")
        for pat, count, sample in m["pedagogical"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if m["royal_we"]:
        lines.append("Royal-we / 'as a society':")
        for pat, count, sample in m["royal_we"]:
            lines.append(f"  - \"{sample}\" ×{count}")
    if m["whether_or_openers"]:
        lines.append(f"'Whether you're X or Y' openers: {m['whether_or_openers']}")
    lines.append("")

    # Low severity
    l = result["low"]
    lines.append("--- LOW SEVERITY ---")
    if l["magic_adverbs"]:
        lines.append("Magic adverbs:")
        for adv, count in l["magic_adverbs"]:
            note = " (survives only when contrasting reality with theory)" if adv == "actually" else ""
            lines.append(f"  - \"{adv}\" ×{count}{note}")
    if l["short_sentence_clusters"]:
        lines.append(f"Short-sentence clusters: {len(l['short_sentence_clusters'])}")
        for run in l["short_sentence_clusters"][:2]:
            for idx, sent, wc in run:
                lines.append(f"  - Sentence {idx+1} ({wc}w): \"{sent[:80]}\"")
    if l["bigram_repetition"]:
        lines.append(f"Bigram repetition (5+ uses): {len(l['bigram_repetition'])}")
        for bg, count in l["bigram_repetition"][:5]:
            lines.append(f"  - \"{bg[0]} {bg[1]}\" ×{count}")
    if l["markdown_tells"]:
        lines.append("Markdown / formatting tells:")
        for tell, val in l["markdown_tells"].items():
            lines.append(f"  - {tell}: {val}")
    lines.append("")

    lines.append("=" * 70)
    lines.append("Note: scanner catches mechanical violations only.")
    lines.append("Qualitative patterns (the actual force of metaphors, real-vs-")
    lines.append("decorative judgment, voice consistency) require reading.")
    lines.append("=" * 70)
    return "\n".join(lines)


def format_quick(result):
    """Compact one-screen output for embedding in other skills."""
    lines = []
    lines.append(f"Verdict: {result['verdict']} (density {result['density']})")
    lines.append(
        f"Violations: {result['totals']['high']}H, "
        f"{result['totals']['medium']}M, {result['totals']['low']}L"
    )
    burst = result["stats"]["burstiness"]
    lines.append(f"Burstiness: {burst if burst is not None else 'n/a'}")
    lines.append(f"Genre: {result['stats']['detected_genre']} | Fingerprint: {result['stats']['model_fingerprint']}")

    # Top fixes — pick the highest-count items
    fixes = []
    for phrase, count in result["high"]["verbs_h"][:2]:
        fixes.append(f"\"{phrase}\" ×{count}")
    for phrase, count in result["high"]["nouns_h"][:1]:
        fixes.append(f"\"{phrase}\" ×{count}")
    for phrase, count in result["high"]["intensifiers_h"][:1]:
        fixes.append(f"\"{phrase}\" ×{count}")
    if result["high"]["em_dashes"]:
        fixes.append(f"em dashes ×{result['high']['em_dashes']}")
    if result["high"]["sycophancy_open"]:
        fixes.append("opener sycophancy")
    if result["high"]["sycophancy_close"]:
        fixes.append("closer sycophancy")
    if fixes:
        lines.append("Top fixes: " + ", ".join(fixes[:3]))
    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Universal AI-slop scanner — pattern + vocabulary + formatting tell detection."
    )
    parser.add_argument("path", nargs="?", help="Path to a text/markdown file. Reads stdin if omitted.")
    parser.add_argument("--json", action="store_true", help="Output structured JSON.")
    parser.add_argument("--quick", action="store_true", help="Compact one-screen output.")
    parser.add_argument(
        "--genre",
        choices=["casual", "marketing", "academic", "encyclopedic", "fiction"],
        help="Override detected genre. Adjusts severity thresholds per calibration.md §3.",
    )
    parser.add_argument(
        "--strict-em-dash",
        action="store_true",
        help="Treat ALL em dashes as H severity (Mahmoud-mode). Default: clusters only.",
    )
    args = parser.parse_args()

    if args.path:
        try:
            text = Path(args.path).read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"File not found: {args.path}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("Empty input.", file=sys.stderr)
        sys.exit(1)

    result = analyze(text, genre=args.genre, strict_em_dash=args.strict_em_dash)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    elif args.quick:
        print(format_quick(result))
    else:
        print(format_human(result))


if __name__ == "__main__":
    main()
