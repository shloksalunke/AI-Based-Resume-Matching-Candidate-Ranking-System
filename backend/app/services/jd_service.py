import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from app.services.parser_service import (
    extract_text_from_file,
    extract_skills,
    extract_education,
    load_skills_taxonomy,
    get_spacy_model,
)

# Common section header patterns used in job descriptions
PREFERRED_HEADING_REGEX = re.compile(
    r"(?:nice\s+to\s+have|good\s+to\s+have|preferred|bonus|desired|plus\s+if\s+you\s+have)",
    re.IGNORECASE,
)

REQUIRED_HEADING_REGEX = re.compile(
    r"(?:must\s+have|requirements?|required|basic\s+qualifications?|minimum\s+qualifications?|core\s+skills?|what\s+you(?:'ll)?\s+need|qualifications?)",
    re.IGNORECASE,
)

GENERAL_BREAK_HEADING_REGEX = re.compile(
    r"^(?:about\s+us|who\s+we\s+are|benefits|perks|responsibilities|what\s+you\s+will\s+do|overview)[\s:]*$",
    re.IGNORECASE,
)


def split_jd_sections(raw_text: str) -> Tuple[str, str, str]:
    """
    Splits the job description into (general_text, required_text, preferred_text)
    based on section heading keywords. Accepts slashes, ampersands, colons and composite headings
    (e.g. 'Nice to Have / Preferred Qualifications:', 'Requirements / Must Have:').
    """
    lines = raw_text.splitlines()
    required_lines: List[str] = []
    preferred_lines: List[str] = []
    general_lines: List[str] = []

    current_section = "general"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line looks like a section heading (short line, usually under 70 chars, or ends with :)
        is_heading_candidate = len(stripped) <= 75 and (
            stripped.endswith(":") or stripped.startswith(("#", "*", "-")) or len(stripped.split()) <= 8
        )

        if is_heading_candidate:
            if GENERAL_BREAK_HEADING_REGEX.match(stripped):
                current_section = "general"
                continue
            elif PREFERRED_HEADING_REGEX.search(stripped):
                current_section = "preferred"
                continue
            elif REQUIRED_HEADING_REGEX.search(stripped):
                current_section = "required"
                continue

        if current_section == "required":
            required_lines.append(stripped)
        elif current_section == "preferred":
            preferred_lines.append(stripped)
        else:
            general_lines.append(stripped)

    return (
        "\n".join(general_lines),
        "\n".join(required_lines),
        "\n".join(preferred_lines),
    )


def extract_min_experience(raw_text: str) -> float:
    """
    Extracts the minimum required years of experience from the job description.
    Catches 'Experience Level: 3+ years', '3+ years', 'minimum 3 years', 'at least 3 years',
    '3-5 years', and variations, returning the minimum specified years.
    """
    patterns = [
        # Explicit labels: "Experience Level: 3+ years", "Experience: 3+ years", "Experience: 3-5 years"
        r"(?:experience\s+level|experience|exp)\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(?:\+|-\s*\d+)?\s*(?:years?|yrs?)",
        # Range specifications: "3-5 years", "3 to 5 years"
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*\d+(?:\.\d+)?\s*(?:years?|yrs?)",
        # Minimum statements: "at least 3 years", "minimum 3 years", "min 3 years"
        r"(?:at\s+least|minimum|min\.?)\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
        # Plus notations: "3+ years", "3+ yrs"
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)",
        # Descriptive sentences: "3+ years of experience", "3 years of relevant experience"
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:relevant|hands-on|industry|work|professional|software)?\s*(?:experience|exp)",
    ]

    found_exp: List[float] = []
    for pattern in patterns:
        for match in re.finditer(pattern, raw_text, re.IGNORECASE):
            try:
                val = float(match.group(1))
                if 0.5 <= val <= 30:
                    found_exp.append(val)
            except (ValueError, IndexError):
                pass

    if found_exp:
        # Take the minimum valid experience requirement
        return min(found_exp)
    return 0.0


def extract_education_requirements(raw_text: str) -> List[str]:
    """
    Extracts explicit education degree requirements mentioned in the JD.
    """
    education_mentions = extract_education(raw_text)
    degrees: Set[str] = set()

    for item in education_mentions:
        deg = item.get("degree")
        if deg:
            degrees.add(deg.strip())

    # Fallback keyword scan for degrees
    generic_degrees = [
        "Bachelor's", "B.Tech", "B.E.", "B.S.", "Master's", "M.Tech",
        "M.S.", "PhD", "Doctorate", "Computer Science", "Information Technology",
        "Engineering degree",
    ]
    for deg in generic_degrees:
        if re.search(rf"\b{re.escape(deg)}\b", raw_text, re.IGNORECASE):
            degrees.add(deg)

    return sorted(list(degrees))


def extract_keywords(raw_text: str, top_n: int = 15) -> List[str]:
    """
    Extracts key domain terminology and nouns from the JD using spaCy or token frequency.
    """
    nlp = get_spacy_model()
    stop_words = {
        "experience", "team", "work", "role", "candidate", "responsibilities",
        "qualifications", "opportunity", "company", "ability", "skills", "knowledge",
        "requirements", "years", "working", "environment", "technologies",
    }
    keywords: List[str] = []

    if nlp:
        doc = nlp(raw_text[:4000])  # limit processing to first 4000 chars for speed
        noun_counts: Dict[str, int] = {}
        for chunk in doc.noun_chunks:
            cleaned = chunk.text.strip().lower()
            if 3 < len(cleaned) < 30 and cleaned not in stop_words and not cleaned.isnumeric():
                noun_counts[cleaned] = noun_counts.get(cleaned, 0) + 1
        sorted_nouns = sorted(noun_counts.items(), key=lambda x: x[1], reverse=True)
        keywords = [k for k, _ in sorted_nouns[:top_n]]

    if not keywords:
        # Regex fallback
        words = re.findall(r"\b[A-Za-z]{4,20}\b", raw_text.lower())
        counts: Dict[str, int] = {}
        for w in words:
            if w not in stop_words:
                counts[w] = counts.get(w, 0) + 1
        sorted_words = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        keywords = [w for w, _ in sorted_words[:top_n]]

    return keywords


def extract_core_skills(
    title: str,
    raw_text: str,
    required_skills: List[str],
    req_text: str = "",
) -> List[str]:
    """
    Identifies core skills from the required skills list:
    1. Required skills that appear in the job title
    2. Required skills mentioned 3+ times in the JD text
    3. The first 2 skills in the required section
    """
    if not required_skills:
        return []

    core_candidates: Set[str] = set()
    title_lower = title.lower()
    raw_lower = raw_text.lower()

    for skill in required_skills:
        s_lower = skill.lower()
        # 1. Appears in job title
        if re.search(rf"\b{re.escape(s_lower)}\b", title_lower):
            core_candidates.add(skill)
            continue

        # 2. Mentioned 3+ times in JD text
        occurrences = len(re.findall(rf"\b{re.escape(s_lower)}\b", raw_lower))
        if occurrences >= 3:
            core_candidates.add(skill)
            continue

    # 3. First 2 skills in the required section
    if req_text:
        skill_positions = []
        for skill in required_skills:
            pos = req_text.lower().find(skill.lower())
            if pos != -1:
                skill_positions.append((pos, skill))
        skill_positions.sort(key=lambda x: x[0])
        for _, skill in skill_positions[:2]:
            core_candidates.add(skill)
    elif len(required_skills) >= 2:
        for s in required_skills[:2]:
            core_candidates.add(s)

    # Preserve order of required skills
    return [s for s in required_skills if s in core_candidates]


def parse_job_description(raw_text: str, title: str = "") -> Dict[str, Any]:
    """
    Parses full JD text into structured fields: required_skills, core_skills,
    preferred_skills, min_experience, education, and keywords.
    """
    gen_text, req_text, pref_text = split_jd_sections(raw_text)

    # Infer title from text if not provided
    if not title:
        first_line = raw_text.strip().splitlines()[0]
        title_match = re.search(r"(?:job\s+title|role|position)\s*[:\-]\s*(.+)", first_line, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else first_line[:60].strip()

    # Extract skills for each partition
    req_skills = extract_skills(req_text)
    pref_skills = extract_skills(pref_text)
    all_skills = extract_skills(raw_text)

    # If no distinct sections are identified, treat all extracted skills as required
    if not req_skills and not pref_skills:
        req_skills = all_skills
        pref_skills = []
    else:
        # Ensure preferred skills do not duplicate required skills
        pref_skills = [s for s in pref_skills if s not in req_skills]
        # Any skills from general text that weren't captured into preferred can default to required
        for s in all_skills:
            if s not in req_skills and s not in pref_skills:
                req_skills.append(s)

    sorted_req = sorted(list(set(req_skills)))
    sorted_pref = sorted(list(set(pref_skills)))
    core_skills = extract_core_skills(title, raw_text, sorted_req, req_text)

    min_exp = extract_min_experience(raw_text)
    edu = extract_education_requirements(raw_text)
    keywords = extract_keywords(raw_text)

    return {
        "required_skills": sorted_req,
        "core_skills": core_skills,
        "preferred_skills": sorted_pref,
        "min_experience": min_exp,
        "education": edu,
        "keywords": keywords,
    }


def parse_job_file(file_path: str, title: str = "") -> Tuple[str, Dict[str, Any]]:
    """
    Extracts text from a file (PDF/DOCX/TXT) and parses the JD structure.
    """
    raw_text = extract_text_from_file(file_path)
    parsed = parse_job_description(raw_text, title=title)
    return raw_text, parsed
