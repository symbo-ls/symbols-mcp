"""Ranked section search over the skills bundle (search_symbols_docs).

The tool used to scan the skill files in directory order and return the first
file in which ANY query word appeared, with a snippet around the first line
holding any word. A multi-word query found the wrong file: for
"prepareDesignSystem pages false object" the common words "pages", "false"
and "object" matched first, in files that never name `prepareDesignSystem`.

Now every skill file is split into sections (one per Markdown heading, code
fences respected) and each section is scored:

- BM25 over the sections, so a term that is in every file ("false",
  "object") weighs little and a rare one (`prepareDesignSystem`) weighs much;
- identifier-like terms (camelCase, `dotted.path`, `snake_case`, `$x`) weigh
  three times a plain word, and a section that misses one of them drops to a
  quarter of its score — the option name the agent asks for must be there;
- a term in the section's heading path counts again;
- the score is multiplied by the square of the (weighted) share of the query
  the section covers, so a section that has all the words beats one that
  repeats one of them;
- the whole query as a phrase in the section is a bonus.

The best sections across all files come back, at most two per file.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

HEADING = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
WORD = re.compile(r"[a-z0-9_$]+")

# Words that carry no meaning in a docs query.
STOP_WORDS = frozenset(
    """
    a an the and or of to in on at by for with from into as is are be been was were it its
    this that these those how what when where which who why do does did can could should
    would will i me my we our you your use using used get set via vs not no yes about
    """.split()
)

IDENTIFIER_WEIGHT = 3.0
WORD_WEIGHT = 1.0
PART_WEIGHT = 0.6
HEADING_BONUS = 1.5
MISSING_IDENTIFIER_FACTOR = 0.25
PHRASE_BONUS = 1.5
PER_FILE = 2
K1 = 1.2
B = 0.75


@dataclass
class Section:
    file: str
    heading: str  # "Title > Section > Subsection"
    line: int  # 1-based line of the heading in its file
    lines: list[str]
    text: str = ""
    heading_text: str = ""
    length: int = 0

    def __post_init__(self) -> None:
        self.text = "\n".join(self.lines).lower()
        self.heading_text = self.heading.lower()
        self.length = max(1, len(WORD.findall(self.text)))


@dataclass
class Term:
    text: str
    weight: float
    identifier: bool
    parts: list[str] = field(default_factory=list)


def is_identifier(token: str) -> bool:
    """camelCase, dotted.path, snake_case, $var, kebab-with-digits are identifiers."""
    if re.search(r"[a-z][A-Z]", token):
        return True
    if re.search(r"\w[._$]\w", token) or token.startswith("$"):
        return True
    return False


def parse_query(query: str) -> list[Term]:
    terms: list[Term] = []
    seen: set[str] = set()
    for raw in re.split(r"[\s,;]+", query or ""):
        token = raw.strip("`'\"()[]{}<>?!:;,")
        # `name:` / `name()` / `name=`: the bare name
        token = re.sub(r"(\(\)|=.*)$", "", token)
        if not token:
            continue
        lower = token.lower()
        if lower in seen:
            continue
        if is_identifier(token):
            parts = [p for p in re.split(r"[._$]+", lower) if len(p) > 1 and p != lower]
            terms.append(Term(lower, IDENTIFIER_WEIGHT, True, parts))
        else:
            if lower in STOP_WORDS or len(lower) < 2:
                continue
            terms.append(Term(lower, WORD_WEIGHT, False))
        seen.add(lower)
    return terms


def split_sections(name: str, content: str) -> list[Section]:
    sections: list[Section] = []
    path: list[str] = []
    current: list[str] = []
    start = 1
    heading = name
    in_fence = False
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if FENCE.match(line):
            in_fence = not in_fence
        m = None if in_fence else HEADING.match(line)
        if m:
            if any(s.strip() for s in current):
                sections.append(Section(name, heading, start, current))
            level = len(m.group(1))
            title = m.group(2).strip()
            path = path[: level - 1] + [""] * max(0, level - 1 - len(path)) + [title]
            heading = " > ".join(p for p in path if p)
            current = [line]
            start = i + 1
        else:
            current.append(line)
    if any(s.strip() for s in current):
        sections.append(Section(name, heading, start, current))
    return sections


def _count(term: str, identifier: bool, text: str) -> int:
    if identifier:
        return text.count(term)
    return len(re.findall(r"(?<![a-z0-9_])" + re.escape(term), text))


class DocsIndex:
    """The sections of every *.md file in a directory, rebuilt when a file changes."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self._signature: tuple | None = None
        self.sections: list[Section] = []
        self.avg_length = 1.0

    def _files(self) -> list[Path]:
        return sorted(self.directory.glob("*.md"))

    def refresh(self) -> None:
        files = self._files()
        signature = tuple((f.name, f.stat().st_mtime_ns, f.stat().st_size) for f in files)
        if signature == self._signature:
            return
        sections: list[Section] = []
        for f in files:
            sections.extend(split_sections(f.name, f.read_text(encoding="utf-8")))
        self.sections = sections
        self.avg_length = (sum(s.length for s in sections) / len(sections)) if sections else 1.0
        self._signature = signature

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        self.refresh()
        terms = parse_query(query)
        if not terms:
            return []
        n = len(self.sections)
        df: dict[str, int] = {}
        counts: list[dict[str, int]] = []
        for s in self.sections:
            c: dict[str, int] = {}
            for t in terms:
                k = _count(t.text, t.identifier, s.text)
                if k:
                    c[t.text] = k
                for p in t.parts:
                    pk = _count(p, False, s.text)
                    if pk:
                        c["part:" + p] = pk
            counts.append(c)
            for key in c:
                df[key] = df.get(key, 0) + 1

        def idf(key: str) -> float:
            d = df.get(key, 0)
            return math.log(1 + (n - d + 0.5) / (d + 0.5))

        identifiers = [t for t in terms if t.identifier]
        phrase = " ".join(t.text for t in terms) if len(terms) > 1 else None
        total = sum(t.weight * idf(t.text) for t in terms) or 1.0

        scored: list[tuple[float, Section]] = []
        for s, c in zip(self.sections, counts):
            if not c:
                continue
            norm = K1 * (1 - B + B * s.length / self.avg_length)
            score = 0.0
            covered = 0.0
            missing_identifier = False
            for t in terms:
                tf = c.get(t.text, 0)
                weight = t.weight * idf(t.text)
                if tf:
                    score += weight * tf * (K1 + 1) / (tf + norm)
                    covered += weight
                    if t.text in s.heading_text:
                        score += weight * HEADING_BONUS
                    continue
                # An identifier written apart (`fetch: { early: { script } }`):
                # every part present counts for less than the whole name.
                if t.parts and all(c.get("part:" + p) for p in t.parts):
                    part_tf = min(c["part:" + p] for p in t.parts)
                    score += PART_WEIGHT * weight * part_tf * (K1 + 1) / (part_tf + norm)
                    covered += PART_WEIGHT * weight
                    continue
                if t.identifier:
                    missing_identifier = True
            if score <= 0:
                continue
            score *= (covered / total) ** 2
            if missing_identifier and identifiers:
                score *= MISSING_IDENTIFIER_FACTOR
            if phrase and phrase in s.text:
                score *= PHRASE_BONUS
            scored.append((score, s))

        scored.sort(key=lambda x: (-x[0], x[1].file, x[1].line))
        limit = max(1, min(int(max_results or 3), 5))
        out: list[dict] = []
        per_file: dict[str, int] = {}
        for score, s in scored:
            if per_file.get(s.file, 0) >= PER_FILE:
                continue
            per_file[s.file] = per_file.get(s.file, 0) + 1
            out.append({
                "file": s.file,
                "section": s.heading,
                "line": s.line,
                "score": round(score, 3),
                "snippet": snippet(s, terms),
            })
            if len(out) >= limit:
                break
        return out


def snippet(section: Section, terms: list[Term], size: int = 22) -> str:
    """The section's heading, then the window around its line richest in query terms."""
    lines = section.lines
    best, best_hits = 0, -1.0
    for i, line in enumerate(lines):
        low = line.lower()
        hits = sum(t.weight for t in terms if _count(t.text, t.identifier, low))
        if hits > best_hits:
            best, best_hits = i, hits
    start = max(0, best - 3)
    window = lines[start:start + size]
    if start > 0:
        window = [lines[0], "…"] + window
    return "\n".join(window).strip("\n")
