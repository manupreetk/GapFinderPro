# analyzer.py
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from rapidfuzz import process, fuzz

_WORD = re.compile(r"[a-zA-Z][a-zA-Z+\-\.#]*")  # keeps tokens like C++, Node.js, React, etc.

def load_roles(path: str | Path) -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()

def ngrams(tokens: List[str], n: int) -> List[str]:
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def to_candidates(text: str) -> Set[str]:
    raw = _WORD.findall(text.lower())
    toks = [t for t in raw if t]
    cands: Set[str] = set()
    for n in (1, 2, 3):
        for g in ngrams(toks, n):
            cands.add(g)
    return cands

def build_skill_bank(roles: Dict) -> List[str]:
    bank: Set[str] = set()
    for r in roles.values():
        for k in ("core", "tools", "nice_to_have"):
            bank.update(r.get(k, []))
    # normalize case but preserve canonical casing by returning unique lower set but mapping later
    return sorted(bank)

def fuzzy_pick(cands: Set[str], bank: List[str], threshold: int = 88) -> Tuple[Set[str], Dict[str, str]]:
    """
    Returns canonical skills found and a map: found_phrase -> canonical_skill
    """
    found: Set[str] = set()
    mapping: Dict[str, str] = {}
    # RapidFuzz is fast but still don't loop bank x cands blindly with heavy scorers
    for phrase in cands:
        # skip junk
        if len(phrase) < 2:
            continue
        match = process.extractOne(
            phrase,
            bank,
            scorer=fuzz.token_set_ratio
        )
        if match and match[1] >= threshold:
            canonical = match[0]
            found.add(canonical)
            mapping[phrase] = canonical
    return found, mapping

def score_against_role(user_skills: Set[str], role_spec: Dict, exp_level: str) -> Dict:
    core = set(role_spec.get("core", []))
    tools = set(role_spec.get("tools", []))
    nice = set(role_spec.get("nice_to_have", []))

    matched_core = sorted(core & user_skills)
    matched_tools = sorted(userskill for userskill in user_skills if userskill in tools)
    matched_nice = sorted(user_skills & nice)

    missing_core = sorted(core - user_skills)
    missing_tools = sorted(tools - user_skills)
    missing_nice = sorted(nice - user_skills)

    # weights tuned per experience
    weights_by_exp = {
        "Beginner (0-1 years)": (0.7, 0.2, 0.1),
        "Intermediate (1-3 years)": (0.6, 0.25, 0.15),
        "Advanced (3+ years)": (0.5, 0.3, 0.2)
    }
    w_core, w_tools, w_nice = weights_by_exp.get(exp_level, (0.6, 0.25, 0.15))

    def cov(matched, total):
        return 1.0 if not total else len(matched) / len(total)

    score = (
        w_core * cov(matched_core, core) +
        w_tools * cov(matched_tools, tools) +
        w_nice * cov(matched_nice, nice)
    ) * 100.0

    # extra penalty if any core is missing completely
    if core and len(matched_core) == 0:
        score *= 0.85

    # top keyword suggestions: first 5 of missing with core priority
    prioritized_missing = (missing_core + missing_tools + missing_nice)[:5]

    return {
        "ats_score": round(score, 2),
        "matched": {
            "core": matched_core,
            "tools": matched_tools,
            "nice_to_have": matched_nice
        },
        "missing": {
            "core": missing_core,
            "tools": missing_tools,
            "nice_to_have": missing_nice
        },
        "top_keywords_to_add": prioritized_missing
    }

def recommend_courses(missing: Dict[str, List[str]]) -> List[Dict]:
    items = []
    for bucket, skills in missing.items():
        for s in skills:
            items.append({
                "skill": s,
                "why": f"Required: {bucket.replace('_', ' ')} for the target role.",
                "suggest": [
                    f"Take a project implementing {s}",
                    f"Search: 'best {s} course beginner'",
                    f"Add a bullet in resume proving {s} with metrics"
                ]
            })
    return items
