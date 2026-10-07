"""
search.py

Finds the most relevant policy section for a given question, and supports
restricting sections by role (Employee / Manager / HR).

Why no ML library: for a short FAQ document like ours, a simple word-overlap
score works just as well as a heavier approach, is instant to run, and is
far easier to explain to a judge in one sentence: "we check how many
meaningful words the question shares with each section, and pick the
section that shares the most."
"""

import re

ALL_ROLES = {"employee", "manager", "hr"}

# A section with no [role: ...] tag is visible to everyone.
_ROLE_TAG_RE = re.compile(r"\[role:\s*([a-zA-Z,\s]+)\]")


def load_sections(filepath="policy.txt"):
    """
    Reads policy.txt and splits it into sections.
    Each section starts with a line beginning with '## '.
    A title can optionally end with a role tag, e.g.:
        ## Termination and Disciplinary Procedures [role: hr]
    which restricts that section to the listed roles. No tag = visible
    to everyone (employee, manager, hr).

    Returns a list of dicts: {"title": ..., "content": ..., "roles": {...}}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    raw_sections = re.split(r"\n(?=## )", text.strip())
    sections = []
    for raw in raw_sections:
        raw = raw.strip()
        if not raw:
            continue
        lines = raw.split("\n", 1)
        title_line = lines[0].replace("##", "").strip()
        content = lines[1].strip() if len(lines) > 1 else ""

        match = _ROLE_TAG_RE.search(title_line)
        if match:
            roles = {r.strip().lower() for r in match.group(1).split(",")}
            title = title_line[: match.start()].strip()
        else:
            roles = set(ALL_ROLES)
            title = title_line

        sections.append({"title": title, "content": content, "roles": roles})
    return sections


def filter_by_role(sections, role):
    """
    Returns only the sections a given role is allowed to see.
    This is the "scope answers to what the user is allowed to see" piece -
    an Employee asking about termination procedures simply won't find a
    matching section, because it's filtered out before search even runs.
    """
    role = role.lower()
    return [s for s in sections if role in s["roles"]]


# Common words that don't help tell sections apart - ignoring them
# makes the match score more meaningful.
_STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "does", "i", "my", "me", "can",
    "what", "how", "many", "much", "for", "of", "to", "in", "on", "get",
    "will", "if", "and", "or", "about", "need", "have", "has", "our",
    "we", "us", "it", "its", "be", "am", "was", "were",
}


def _normalize(text):
    """Lowercase, strip punctuation, split into words, drop stopwords."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS}


def find_best_section(question, sections):
    """
    Scores every section against the question by word overlap, counting a
    word that appears in the section TITLE twice as strongly as one that
    only appears in the body text. (Without this, a word like "termination"
    mentioned once in an unrelated section's body can outscore the section
    actually named "Termination" - title matches are the stronger signal.)

    Returns (best_section, score) where score is 0.0-1.0.
    A None best_section (or a low score) means: nothing matched well
    enough, so the app should say "not sure, contact HR" instead of
    guessing.
    """
    question_words = _normalize(question)
    if not question_words:
        return None, 0.0

    best_section = None
    best_score = 0.0

    for section in sections:
        title_words = _normalize(section["title"])
        content_words = _normalize(section["content"])

        weighted = 0
        for w in question_words:
            if w in title_words:
                weighted += 2
            elif w in content_words:
                weighted += 1

        score = weighted / (len(question_words) * 2)

        if score > best_score:
            best_score = score
            best_section = section

    return best_section, best_score
