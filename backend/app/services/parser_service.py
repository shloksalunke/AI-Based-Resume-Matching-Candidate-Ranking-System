import os
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import pdfplumber
import docx

# Global cached resources
_SPACY_NLP = None
_SKILLS_TAXONOMY = None


def get_spacy_model():
    """
    Lazy loader for spaCy en_core_web_sm pipeline.
    Falls back gracefully if the model is not yet downloaded.
    """
    global _SPACY_NLP
    if _SPACY_NLP is None:
        try:
            import spacy
            _SPACY_NLP = spacy.load("en_core_web_sm")
        except Exception:
            try:
                import spacy
                _SPACY_NLP = spacy.blank("en")
            except Exception:
                _SPACY_NLP = None
    return _SPACY_NLP


def load_skills_taxonomy() -> Dict[str, Any]:
    """
    Loads skills taxonomy JSON containing categories and alias mappings.
    """
    global _SKILLS_TAXONOMY
    if _SKILLS_TAXONOMY is None:
        taxonomy_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "skills_taxonomy.json"
        )
        if os.path.exists(taxonomy_path):
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                _SKILLS_TAXONOMY = json.load(f)
        else:
            _SKILLS_TAXONOMY = {"categories": {}}
    return _SKILLS_TAXONOMY


def extract_text_from_pdf(file_path: str) -> str:
    """Extracts raw text content from all pages of a PDF document."""
    extracted_text_pieces: List[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text_pieces.append(text)
    return "\n".join(extracted_text_pieces)


def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from paragraphs and tables of a DOCX document."""
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    
    # Also extract any text contained in tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)
                
    return "\n".join(paragraphs)


def extract_text_from_file(file_path: str) -> str:
    """
    Auto-detects file extension and extracts plain text from PDF or DOCX files.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    else:
        # Fallback to UTF-8 text read if plain text file
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def extract_email(text: str) -> Optional[str]:
    """Extracts the first valid email address from text using regex."""
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0).strip() if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extracts a valid telephone number supporting standard international & local formats."""
    patterns = [
        r"(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
        r"(?:\+91[\s-]?)?[6789]\d{9}",
        r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(0).strip()
            # Basic validation to avoid simple numbers like '2019-2023'
            digits_only = re.sub(r"\D", "", candidate)
            if len(digits_only) >= 10:
                return candidate
    return None


REJECT_NAME_WORDS = re.compile(
    r"\b(engineer|developer|analyst|architect|consultant|specialist|manager|lead|"
    r"administrator|intern|associate|designer|programmer|coder|director|scientist|"
    r"qa|tester|technologies|solutions|systems|services|innovations|corp|inc|ltd|"
    r"java|python|javascript|typescript|spring|react|angular|node|c\+\+|c\#|aws|cloud|"
    r"resume|curriculum|vitae|summary|profile|objective|experience|education|skills|"
    r"projects|certifications|contact|page|phone|email|professional)\b",
    re.IGNORECASE,
)


def extract_name_from_email(email_str: str) -> Optional[str]:
    """Derives a formatted candidate name from an email local-part (e.g. aditya.joshi -> Aditya Joshi)."""
    if not email_str or "@" not in email_str:
        return None
    local_part = email_str.split("@")[0]
    parts = [re.sub(r"\d+", "", p).strip() for p in re.split(r"[._-]", local_part)]
    name_parts = [p.capitalize() for p in parts if len(p) >= 2 and p.isalpha()]
    if len(name_parts) >= 2:
        return " ".join(name_parts[:3])
    elif len(name_parts) == 1:
        return name_parts[0]
    return None


def extract_name(text: str) -> Optional[str]:
    """
    Extracts candidate name from the top non-empty lines of text.
    Rejects lines containing emails, phone numbers, digits, URLs, or role/technical words.
    Prefers single-line spaCy PERSON entities, valid capitalized words, or email local-part fallback.
    Never returns a string containing newlines.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    email = extract_email(text)
    nlp = get_spacy_model()

    # Consider only the first 5 non-empty lines
    for line in lines[:5]:
        line_clean = line.strip(" ,|•-")

        # Disqualify line if it contains newline, email, digits, or URLs
        if "\n" in line_clean or "@" in line_clean:
            continue
        if re.search(r"\d", line_clean):
            continue
        if re.search(r"https?://|www\.|\.com|\.org|\.net|\.in|\.edu|\.io", line_clean, re.IGNORECASE):
            continue

        # Disqualify line if it contains role or technical keywords
        if REJECT_NAME_WORDS.search(line_clean):
            continue

        words = line_clean.split()
        if not (2 <= len(words) <= 4):
            continue

        # Prefer spaCy PERSON entity on this single clean line
        if nlp:
            doc = nlp(line_clean)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    ent_text = ent.text.strip()
                    if 2 <= len(ent_text.split()) <= 4 and "\n" not in ent_text:
                        return ent_text

        # Heuristic: all words are capitalized alphabetic tokens
        if all(w[0].isupper() and w.isalpha() for w in words):
            return line_clean

    # Fallback to local-part of extracted email
    if email:
        fallback_name = extract_name_from_email(email)
        if fallback_name:
            return fallback_name

    return None


def extract_skills(text: str) -> List[str]:
    """
    Extracts canonical skills from text using data/skills_taxonomy.json.
    Matches aliases case-insensitively using exact boundary checks.
    """
    taxonomy = load_skills_taxonomy()
    found_skills: Set[str] = set()
    lowered_text = f" {text.lower()} "

    for category, skill_list in taxonomy.get("categories", {}).items():
        for item in skill_list:
            canonical_name = item["name"]
            aliases = item.get("aliases", [])
            for alias in aliases:
                norm_alias = alias.lower().strip()
                if not norm_alias:
                    continue

                # For special symbols like c++, c#, .net, ci/cd, use non-alphanumeric boundaries
                escaped = re.escape(norm_alias)
                pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"
                if re.search(pattern, lowered_text):
                    found_skills.add(canonical_name)
                    break

    return sorted(list(found_skills))


MONTHS_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

SECTION_HEADINGS = {
    "experience": re.compile(
        r"^(?:work\s+experience|professional\s+experience|employment\s+history|work\s+history|experience|internships?|internship\s+experience|employment)\b",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education|educational\s+qualifications?|academic\s+background|academics|academic\s+history|qualifications?)\b",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:projects?|key\s+projects?|academic\s+projects?|personal\s+projects?|technical\s+projects?)\b",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:skills?|technical\s+skills?|core\s+competencies|technologies|key\s+skills?|tools\s+&?\s+technologies)\b",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:certifications?|licenses?|credentials?|certificates?|achievements?|honors?\s*(?:&|and)\s*awards?)\b",
        re.IGNORECASE,
    ),
    "summary": re.compile(
        r"^(?:summary|professional\s+summary|career\s+objective|objective|about\s+me|profile)\b",
        re.IGNORECASE,
    ),
}

DEGREE_TERMS_REGEX = re.compile(
    r"\b(b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|b\.?s\.?|m\.?s\.?|b\.?sc|m\.?sc|bca|mca|bba|mba|ph\.?d|"
    r"bachelor(?:'s)?|master(?:'s)?|diploma|higher\s+secondary|senior\s+secondary|high\s+school|"
    r"secondary\s+school|class\s+x|class\s+xii|10th|12th|hsc|ssc|cbse|icse|matriculation)\b",
    re.IGNORECASE,
)

INSTITUTION_TERMS_REGEX = re.compile(
    r"\b(university|institute|college|school|academy|vidyalaya|polytechnic|campus|iit|nit|iiit|bits|vit)\b",
    re.IGNORECASE,
)


def segment_resume_lines(text: str) -> List[Tuple[str, str]]:
    """
    Tags each non-empty line of text with its enclosing section name
    ('header', 'summary', 'experience', 'education', 'projects', 'skills', 'certifications', 'other').
    """
    lines = [line.strip() for line in text.splitlines()]
    tagged: List[Tuple[str, str]] = []
    current_section = "header"

    for line in lines:
        if not line:
            continue

        clean_heading = re.sub(r"[:\-_|•*#]+", "", line).strip()
        matched_section = None
        words = clean_heading.split()
        if 1 <= len(words) <= 5:
            for sec_name, pattern in SECTION_HEADINGS.items():
                if pattern.match(clean_heading):
                    matched_section = sec_name
                    break

        if matched_section:
            current_section = matched_section
        else:
            tagged.append((current_section, line))

    return tagged


def extract_total_experience_years(text: str) -> float:
    """
    Computes total years of experience accurately:
    1. Checks direct textual claims (e.g. '5+ years of experience').
    2. Sums non-overlapping date ranges from WORK/INTERNSHIP experience only.
    3. Strictly ignores date ranges that belong to Education or degree lines (e.g. '2020 - 2024' for B.Tech).
    4. For freshers/entry-level with no full-time experience, avoids false positives.
    """
    # 1. Direct regex search for statements like "X years of experience"
    explicit_years = 0.0
    phrase_matches = re.findall(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)",
        text,
        re.IGNORECASE,
    )
    if phrase_matches:
        try:
            explicit_years = max(float(val) for val in phrase_matches)
        except ValueError:
            pass

    # Check for explicit month statements like "1 month internship", "3 months experience", "duration: 1 month"
    month_phrase_matches = re.findall(
        r"(\d+)\s+months?(?:\s+of)?\s+(?:experience|exp|internship)",
        text,
        re.IGNORECASE,
    )
    if not month_phrase_matches:
        month_phrase_matches = re.findall(
            r"(?:duration|period)\s*[:\-]\s*(\d+)\s+months?",
            text,
            re.IGNORECASE,
        )
    if month_phrase_matches:
        try:
            month_years = max(round(int(m) / 12.0, 2) for m in month_phrase_matches)
            if explicit_years == 0.0:
                explicit_years = month_years
        except ValueError:
            pass

    tagged_lines = segment_resume_lines(text)

    # Check if the candidate explicitly identifies as fresher
    is_fresher = bool(re.search(r"\b(fresher|recent\s+graduate|entry[\s-]*level|seeking\s+(?:an?\s+)?entry)\b", text, re.IGNORECASE))
    if is_fresher and explicit_years == 0.0:
        exp_lines = [l for sec, l in tagged_lines if sec == "experience"]
        if not exp_lines:
            return 0.0

    current_year = datetime.now().year
    current_month = datetime.now().month
    date_intervals: List[Tuple[float, float]] = []

    month_regex = (
        r"(?i)\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"[,\s]+(20\d\d|19\d\d)\s*(?:-|–|—|to)\s*"
        r"(present|current|now|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[,\s]+(20\d\d|19\d\d))"
    )

    year_regex = r"\b(20\d\d|19\d\d)\s*(?:-|–|—|to)\s*(present|current|now|20\d\d|19\d\d)\b"

    for sec_name, line in tagged_lines:
        if sec_name == "education":
            continue
        if DEGREE_TERMS_REGEX.search(line):
            continue
        if INSTITUTION_TERMS_REGEX.search(line) and not re.search(r"\b(intern|internship|developer|engineer|analyst)\b", line, re.IGNORECASE):
            continue

        month_found = False
        for match in re.finditer(month_regex, line):
            month_found = True
            start_m_str, start_y_str, end_raw, *rest = match.groups()
            start_m = MONTHS_MAP.get(start_m_str.lower(), 1)
            start_y = int(start_y_str)
            start_dec = start_y + (start_m - 1) / 12.0

            if any(term in end_raw.lower() for term in ["present", "current", "now"]):
                end_dec = current_year + current_month / 12.0
            else:
                end_parts = end_raw.strip().split()
                if len(end_parts) >= 2:
                    end_m = MONTHS_MAP.get(end_parts[0].lower(), 12)
                    try:
                        end_y = int(end_parts[-1])
                    except ValueError:
                        end_y = current_year
                    # End month is inclusive (up to end of that month)
                    end_dec = end_y + end_m / 12.0
                else:
                    end_dec = current_year + current_month / 12.0

            if end_dec >= start_dec and (end_dec - start_dec) <= 40:
                date_intervals.append((start_dec, end_dec))

        single_month_regex = (
            r"(?i)\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
            r"[,\s]+(20\d\d|19\d\d)\b"
        )

        if not month_found and (sec_name == "experience" or re.search(r"\b(intern|internship|developer|engineer|lead|consultant|manager|trainee|analyst|associate|role|position|project)\b", line, re.IGNORECASE)):
            sm_match = re.search(single_month_regex, line)
            if sm_match:
                sm_str, sy_str = sm_match.groups()
                sm_val = MONTHS_MAP.get(sm_str.lower(), 1)
                sy_val = int(sy_str)
                s_dec = sy_val + (sm_val - 1) / 12.0
                e_dec = sy_val + sm_val / 12.0  # Exactly 1 full month duration
                date_intervals.append((s_dec, e_dec))
                month_found = True

        if not month_found and (sec_name == "experience" or re.search(r"\b(intern|internship|developer|engineer|lead|consultant|manager|trainee|analyst|associate)\b", line, re.IGNORECASE)):
            for match in re.finditer(year_regex, line, re.IGNORECASE):
                start_y = int(match.group(1))
                end_val = match.group(2).lower()
                start_dec = float(start_y)
                if end_val in ["present", "current", "now"]:
                    end_dec = float(current_year) + (current_month / 12.0)
                else:
                    end_y = int(end_val)
                    if end_y == start_y:
                        end_dec = float(end_y) + 0.25
                    else:
                        end_dec = float(end_y)

                if end_dec >= start_dec and (end_dec - start_dec) <= 40:
                    date_intervals.append((start_dec, end_dec))

    calculated_years = 0.0
    if date_intervals:
        date_intervals.sort(key=lambda x: x[0])
        merged: List[Tuple[float, float]] = []
        for interval in date_intervals:
            if not merged:
                merged.append(interval)
            else:
                prev_start, prev_end = merged[-1]
                if interval[0] <= prev_end:
                    merged[-1] = (prev_start, max(prev_end, interval[1]))
                else:
                    merged.append(interval)
        calculated_years = sum(end - start for start, end in merged)

    final_experience = max(explicit_years, round(calculated_years, 1))
    return min(final_experience, 40.0)


def extract_companies_and_designations(text: str) -> List[Dict[str, str]]:
    """
    Extracts employment roles and organizations matching software/tech designations.
    Extracts from both explicit patterns ('Role at Company') and from the Experience section.
    """
    results: List[Dict[str, str]] = []
    seen_roles: Set[str] = set()

    designation_patterns = [
        r"(?:senior\s+|lead\s+|principal\s+|staff\s+|junior\s+|associate\s+|trainee\s+|intern\s+)?(?:software\s+|frontend\s+|front-end\s+|backend\s+|back-end\s+|full[\s-]?stack\s+|web\s+|mobile\s+|android\s+|ios\s+|java\s+|python\s+|react\s+|node(?:\.js)?\s+|devops\s+|cloud\s+|data\s+|ml\s+|ai\s+|machine\s+learning\s+|qa\s+|test\s+|automation\s+|security\s+|systems?\s+|database\s+)?(?:engineer|developer|architect|designer|analyst|consultant|programmer|specialist|manager|lead|intern|trainee)\b",
        r"\b(?:sde(?:\s*[-–—]?\s*[123iIvV]+)?|tech\s+lead|engineering\s+manager|product\s+manager|solutions?\s+architect|devops\s+engineer|cloud\s+engineer|data\s+scientist|data\s+engineer|data\s+analyst|scrum\s+master)\b",
    ]

    action_verb_prefix = re.compile(
        r"^(?:developed|built|designed|implemented|created|managed|worked|assisted|engineered|optimized|led|maintained|tested|collaborated|automated|wrote|spearheaded|utilized|used)\b",
        re.IGNORECASE,
    )

    tagged_lines = segment_resume_lines(text)

    for idx, (sec_name, line) in enumerate(tagged_lines):
        if sec_name in ["summary", "objective", "education", "skills", "projects", "certifications", "interests", "languages"]:
            continue
        if line.startswith(("-", "•", "*", "–", "—", "(cid:127)")):
            continue
        if action_verb_prefix.match(line):
            continue

        matched_desig = None
        for pattern in designation_patterns:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                matched_desig = m.group(0).strip().title()
                break

        if not matched_desig:
            role_kw = re.search(r"^(?:role|position|designation|title)\s*[:\-]\s*(.+)$", line, re.IGNORECASE)
            if role_kw:
                matched_desig = role_kw.group(1).strip().title()

        if matched_desig:
            company = "Not specified"
            inline_comp = re.search(
                rf"{re.escape(matched_desig)}[\s,-]+(?:at|@|for)?\s+([A-Za-z0-9&.\s]{{2,40}})",
                line,
                re.IGNORECASE,
            )
            if inline_comp:
                cand_comp = inline_comp.group(1).strip(" -|•,")
                if not action_verb_prefix.match(cand_comp) and not re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|20\d\d)\b", cand_comp, re.IGNORECASE):
                    company = cand_comp
            else:
                comp_kw = re.search(r"^(?:company|organization|firm|client)\s*[:\-]\s*(.+)$", line, re.IGNORECASE)
                if comp_kw:
                    company = comp_kw.group(1).strip()
                elif sec_name == "experience":
                    if idx > 0 and tagged_lines[idx - 1][0] == "experience":
                        prev_line = tagged_lines[idx - 1][1]
                        if not prev_line.startswith(("-", "•", "*")) and not action_verb_prefix.match(prev_line) and len(prev_line.split()) <= 6:
                            if not re.search(r"\b(20\d\d|present|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b", prev_line, re.IGNORECASE):
                                company = prev_line.strip()
                    if company == "Not specified" and idx + 1 < len(tagged_lines) and tagged_lines[idx + 1][0] == "experience":
                        next_line = tagged_lines[idx + 1][1]
                        if not next_line.startswith(("-", "•", "*")) and not action_verb_prefix.match(next_line) and len(next_line.split()) <= 6:
                            if not re.search(r"\b(20\d\d|present|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b", next_line, re.IGNORECASE):
                                company = next_line.strip()

            key = f"{matched_desig} - {company}"
            if key not in seen_roles:
                seen_roles.add(key)
                results.append({"designation": matched_desig, "company": company, "raw_line": line})

    return results


def extract_education(text: str) -> List[Dict[str, str]]:
    """
    Extracts degrees, majors, and universities using degree regex heuristics and section awareness.
    Guarantees clean degree, institution, and graduation year fields.
    """
    education_list: List[Dict[str, str]] = []
    seen_degrees: Set[str] = set()

    degree_patterns = [
        (r"\b(B\.?Tech(?:nology)?)\b", "B.Tech"),
        (r"\b(M\.?Tech(?:nology)?)\b", "M.Tech"),
        (r"\b(B\.?E\.?)\b", "B.E"),
        (r"\b(M\.?E\.?)\b", "M.E"),
        (r"\b(B\.?S\.?|B\.?Sc)\b", "B.S"),
        (r"\b(M\.?S\.?|M\.?Sc)\b", "M.S"),
        (r"\b(BCA)\b", "BCA"),
        (r"\b(MCA)\b", "MCA"),
        (r"\b(BBA)\b", "BBA"),
        (r"\b(MBA)\b", "MBA"),
        (r"\b(Bachelor(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?)\b", "Bachelor's"),
        (r"\b(Master(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?)\b", "Master's"),
        (r"\b(Ph\.?D)\b", "Ph.D"),
        (r"\b(Diploma(?:\s+in\s+[A-Za-z\s]+)?)\b", "Diploma"),
        (r"\b(Class\s+XII|12th|Higher\s+Secondary|Senior\s+Secondary|HSC)\b", "Class XII (12th)"),
        (r"\b(Class\s+X|10th|Secondary\s+School|High\s+School|SSC|Matriculation)\b", "Class X (10th)"),
    ]

    tagged_lines = segment_resume_lines(text)

    for idx, (sec_name, line) in enumerate(tagged_lines):
        matched_degree_name = None
        for pattern, std_name in degree_patterns:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                matched_degree_name = std_name
                break

        if matched_degree_name:
            year_match = re.search(r"\b(20\d\d|19\d\d)\b", line)
            year = year_match.group(0) if year_match else None
            institution = "Not specified"

            inst_same_line = re.search(
                r"[-–—|,]\s*([A-Za-z0-9&.\s]{3,60}(?:University|Institute|College|School|Academy|Vidya|Campus|Polytechnic|IIT|NIT|IIIT|BITS|VIT)[A-Za-z0-9&.\s]*)",
                line,
                re.IGNORECASE,
            )
            if inst_same_line:
                institution = inst_same_line.group(1).strip()
            elif idx + 1 < len(tagged_lines):
                next_line = tagged_lines[idx + 1][1]
                if INSTITUTION_TERMS_REGEX.search(next_line):
                    institution = next_line.strip()
                    if not year:
                        y_m = re.search(r"\b(20\d\d|19\d\d)\b", next_line)
                        if y_m:
                            year = y_m.group(0)
                elif idx + 2 < len(tagged_lines) and INSTITUTION_TERMS_REGEX.search(tagged_lines[idx + 2][1]):
                    institution = tagged_lines[idx + 2][1].strip()

            if institution == "Not specified" and INSTITUTION_TERMS_REGEX.search(line):
                institution = line.strip()

            key = f"{matched_degree_name} - {institution}"
            if key not in seen_degrees:
                seen_degrees.add(key)
                education_list.append({
                    "degree": matched_degree_name,
                    "year": year,
                    "institution": institution,
                    "raw": line,
                })

    return education_list


def extract_certifications(text: str) -> List[str]:
    """
    Extracts certifications and licenses from the resume.
    """
    certs: List[str] = []
    cert_keywords = [
        "AWS Certified", "Google Cloud Certified", "Azure Certified", "PMP",
        "CKA", "CKAD", "CompTIA", "CISSP", "Certified Scrum Master", "CSM",
        "HashiCorp Certified", "TensorFlow Developer Certificate"
    ]
    for cert in cert_keywords:
        if re.search(rf"\b{re.escape(cert)}\b", text, re.IGNORECASE):
            certs.append(cert)

    # Also look for lines under a "Certifications" heading
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    in_cert_section = False
    for line in lines:
        if re.match(r"^(?:certifications?|licenses?|credentials?)$", line, re.IGNORECASE):
            in_cert_section = True
            continue
        elif in_cert_section:
            if re.match(r"^(?:education|skills|experience|projects|summary)$", line, re.IGNORECASE):
                in_cert_section = False
            elif line.startswith(("-", "•", "*")):
                cleaned = line.lstrip("-•* ").strip()
                if cleaned and cleaned not in certs:
                    certs.append(cleaned)
    return certs


def extract_projects(text: str) -> List[Dict[str, str]]:
    """
    Extracts projects mentioned in a Projects section or matching bullet points.
    """
    projects: List[Dict[str, str]] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    in_project_section = False
    current_project: Optional[Dict[str, str]] = None

    for line in lines:
        if re.match(r"^(?:projects?|key projects?|academic projects?)$", line, re.IGNORECASE):
            in_project_section = True
            continue
        elif in_project_section:
            if re.match(r"^(?:education|skills|experience|work history|certifications|summary)$", line, re.IGNORECASE):
                in_project_section = False
                if current_project:
                    projects.append(current_project)
                    current_project = None
            elif line.startswith(("-", "•", "*")):
                if current_project:
                    current_project["description"] += " " + line.lstrip("-•* ").strip()
                else:
                    current_project = {"title": line.lstrip("-•* ").strip(), "description": ""}
            elif len(line) < 60 and not line.endswith("."):
                if current_project:
                    projects.append(current_project)
                current_project = {"title": line, "description": ""}

    if current_project:
        projects.append(current_project)

    return projects


def parse_resume_content(filename: str, raw_text: str) -> Dict[str, Any]:
    """
    Unified parser extracting all structured metadata from raw resume text.
    """
    return {
        "filename": filename,
        "raw_text": raw_text,
        "name": extract_name(raw_text),
        "email": extract_email(raw_text),
        "phone": extract_phone(raw_text),
        "skills": extract_skills(raw_text),
        "total_experience_years": extract_total_experience_years(raw_text),
        "companies_and_designations": extract_companies_and_designations(raw_text),
        "education": extract_education(raw_text),
        "certifications": extract_certifications(raw_text),
        "projects": extract_projects(raw_text),
    }


def parse_resume_file(file_path: str) -> Dict[str, Any]:
    """
    Convenience function that reads a file from disk and parses it.
    """
    filename = os.path.basename(file_path)
    raw_text = extract_text_from_file(file_path)
    return parse_resume_content(filename=filename, raw_text=raw_text)
