import re
from typing import Any, Dict, List, Optional, Set, Tuple
from app.services.embedding_service import (
    compute_text_similarity,
    compute_skill_similarity,
)
from app.services.parser_service import load_skills_taxonomy

# Scoring component weights (sum to 100.0)
WEIGHT_SKILLS: float = 40.0
WEIGHT_SEMANTIC: float = 25.0
WEIGHT_EXPERIENCE: float = 20.0
WEIGHT_EDUCATION: float = 10.0
WEIGHT_RELEVANCE: float = 5.0

# Skill weight multipliers
WEIGHT_CORE_SKILL: float = 3.0
WEIGHT_REQUIRED_SKILL: float = 2.0
WEIGHT_PREFERRED_SKILL: float = 1.0

# Core skill gate score cap
CORE_SKILL_GATE_CAP: float = 30.0

# Threshold for semantic skill similarity partial match credit
SEMANTIC_SKILL_THRESHOLD: float = 0.75

# Semantic similarity calibration floor:
# Generic background text similarity between different technical documents typically hovers
# around 0.20-0.25 due to common resume vocabulary (e.g. 'software', 'team', 'experience').
# We calibrate raw cosine similarity by mapping values <= SEMANTIC_SIMILARITY_FLOOR to 0.0,
# and linearly stretching [SEMANTIC_SIMILARITY_FLOOR, 1.0] to [0.0, 1.0] so baseline noise is suppressed.
SEMANTIC_SIMILARITY_FLOOR: float = 0.25

# Generic tooling and soft skills that must not be counted as core required technical matches
# unless explicitly mandated as primary requirements by the job description.
GENERIC_TOOLING_AND_SOFT_SKILLS: Set[str] = {
    "git", "agile / scrum", "agile", "scrum", "communication", "problem solving",
    "collaboration", "time management", "team leadership", "leadership", "adaptability",
    "attention to detail", "continuous learning", "code review", "project management",
}

# Blocklist of known false-positive pairs that must never semantically partial-match
FALSE_POSITIVE_PAIRS: Set[frozenset] = {
    frozenset({"java", "javascript"}),
    frozenset({"c", "c++"}),
    frozenset({"c", "c#"}),
    frozenset({"c++", "c#"}),
    frozenset({"c", "objective-c"}),
    frozenset({"c++", "objective-c"}),
    frozenset({"c#", "objective-c"}),
    frozenset({"go", "golang"}),
    frozenset({"go", "django"}),
    frozenset({"go", "cargo"}),
    frozenset({"r", "rust"}),
    frozenset({"r", "ruby"}),
}


def calibrate_semantic_similarity(raw_sim: float) -> float:
    """
    Calibrates document cosine similarity against the empirical background noise floor.
    Values at or below 0.25 map to 0.0; values between 0.25 and 1.0 scale linearly.
    """
    if raw_sim <= SEMANTIC_SIMILARITY_FLOOR:
        return 0.0
    scaled = (raw_sim - SEMANTIC_SIMILARITY_FLOOR) / (1.0 - SEMANTIC_SIMILARITY_FLOOR)
    return max(0.0, min(1.0, scaled))

_SKILL_CATEGORY_MAP: Optional[Dict[str, str]] = None


def get_skill_category(skill_name: str) -> Optional[str]:
    """
    Looks up the taxonomy category for a canonical skill or alias.
    """
    global _SKILL_CATEGORY_MAP
    if _SKILL_CATEGORY_MAP is None:
        taxonomy = load_skills_taxonomy()
        mapping: Dict[str, str] = {}
        for category, skill_list in taxonomy.get("categories", {}).items():
            for item in skill_list:
                c_name = item.get("name", "").strip().lower()
                if c_name:
                    mapping[c_name] = category
                for alias in item.get("aliases", []):
                    norm_alias = alias.strip().lower()
                    if norm_alias:
                        mapping[norm_alias] = category
        _SKILL_CATEGORY_MAP = mapping
    return _SKILL_CATEGORY_MAP.get(skill_name.strip().lower())


def is_false_positive_pair(skill_a: str, skill_b: str) -> bool:
    """Checks if two skills belong to the explicit false-positive blocklist."""
    pair = frozenset({skill_a.strip().lower(), skill_b.strip().lower()})
    return pair in FALSE_POSITIVE_PAIRS


def evaluate_skills(
    required_skills: List[str],
    preferred_skills: List[str],
    candidate_skills: List[str],
    core_skills: Optional[List[str]] = None,
) -> Tuple[float, List[str], List[str], List[str], List[str]]:
    """
    Evaluates candidate skills against JD required and preferred skills.
    Core skills get weight 3x, other required skills weight 2x, preferred 1x.
    Exact + alias matches receive full (1.0) credit.
    Semantic similarity >= 0.75 receives partial (0.5) credit only if skills
    belong to the same category and are not in the false-positive blocklist.
    """
    reasons: List[str] = []
    matched: Set[str] = set()
    partial: Set[str] = set()
    missing: Set[str] = set()

    candidate_skills_lower = {s.lower(): s for s in candidate_skills}
    core_set = {s.lower().strip() for s in (core_skills or [])}

    # Helper function to evaluate a single skill against candidate pool
    def check_skill(target_skill: str) -> Tuple[float, Optional[str]]:
        target_lower = target_skill.lower().strip()
        # 1. Exact canonical or case-insensitive match
        if target_lower in candidate_skills_lower:
            return 1.0, candidate_skills_lower[target_lower]

        target_cat = get_skill_category(target_skill)

        # 2. Semantic vector similarity match
        best_sim = 0.0
        best_cand = None
        for cand_s in candidate_skills:
            # Check false positive blocklist
            if is_false_positive_pair(target_skill, cand_s):
                continue

            # Only apply semantic matching between skills belonging to the SAME taxonomy category
            cand_cat = get_skill_category(cand_s)
            if not target_cat or not cand_cat or target_cat != cand_cat:
                continue

            sim = compute_skill_similarity(target_skill, cand_s)
            if sim > best_sim:
                best_sim = sim
                best_cand = cand_s

        # Allow 0.70 threshold for validated same-category framework variants (e.g. Spring Boot ~ Spring Framework)
        effective_threshold = 0.70 if (target_cat and target_cat == get_skill_category(best_cand or "")) else SEMANTIC_SKILL_THRESHOLD
        if best_sim >= effective_threshold and best_cand:
            return 0.5, best_cand

        return 0.0, None

    req_points = 0.0
    req_total_possible = sum(
        WEIGHT_CORE_SKILL if s.lower().strip() in core_set else WEIGHT_REQUIRED_SKILL
        for s in required_skills
    )
    req_matched_count = 0
    req_partial_count = 0

    for s in required_skills:
        weight = WEIGHT_CORE_SKILL if s.lower().strip() in core_set else WEIGHT_REQUIRED_SKILL
        credit, matched_name = check_skill(s)
        if credit == 1.0:
            matched.add(s)
            req_points += weight
            req_matched_count += 1
        elif credit == 0.5:
            partial.add(f"{s} (~ {matched_name})")
            req_points += (weight * 0.5)
            req_partial_count += 1
        else:
            missing.add(s)

    pref_points = 0.0
    pref_total_possible = len(preferred_skills) * WEIGHT_PREFERRED_SKILL
    pref_matched_count = 0

    for s in preferred_skills:
        credit, matched_name = check_skill(s)
        if credit == 1.0:
            matched.add(s)
            pref_points += WEIGHT_PREFERRED_SKILL
            pref_matched_count += 1
        elif credit == 0.5:
            partial.add(f"{s} (~ {matched_name})")
            pref_points += (WEIGHT_PREFERRED_SKILL * 0.5)
        else:
            # Preferred skills not owned are noted but don't strictly penalize required pool
            pass

    total_possible_points = req_total_possible + pref_total_possible
    earned_points = req_points + pref_points

    if total_possible_points > 0:
        skills_score = (earned_points / total_possible_points) * WEIGHT_SKILLS
    else:
        # If JD has no specified skills, award default baseline
        skills_score = WEIGHT_SKILLS if candidate_skills else (WEIGHT_SKILLS * 0.5)

    skills_score = round(max(0.0, min(WEIGHT_SKILLS, skills_score)), 1)

    # Human readable reasoning
    if required_skills:
        reasons.append(
            f"Required Skills: matched {req_matched_count}/{len(required_skills)}"
            + (f" ({req_partial_count} partial)" if req_partial_count > 0 else "")
            + f" [{skills_score:.1f}/{WEIGHT_SKILLS} pts]"
        )
    if preferred_skills:
        reasons.append(f"Preferred Skills: matched {pref_matched_count}/{len(preferred_skills)}")
    if missing:
        missing_preview = ", ".join(list(missing)[:5])
        if len(missing) > 5:
            missing_preview += f" (+{len(missing)-5} more)"
        reasons.append(f"Missing required/target skills: {missing_preview}")

    return skills_score, sorted(list(matched)), sorted(list(partial)), sorted(list(missing)), reasons


def evaluate_experience(
    candidate_years: float,
    required_years: float,
    req_matched_count: int = 0,
    num_required_skills: int = 0,
    req_match_ratio: float = 1.0,
    core_matched_count: int = 0,
    num_core_skills: int = 0,
    core_match_ratio: float = 1.0,
) -> Tuple[float, str]:
    """
    Evaluates candidate experience years vs job minimum requirement.
    Full score if candidate_years >= required_years; proportional otherwise.
    Experience score is scaled by a blended match ratio:
    0.6 * core_skill_match_ratio + 0.4 * required_skill_match_ratio (floor 0.25).
    """
    if required_years <= 0.0:
        base_score = WEIGHT_EXPERIENCE
        base_reason = f"No minimum experience required"
    elif candidate_years >= required_years:
        if required_years <= 2.0 and candidate_years >= 12.0:
            base_score = WEIGHT_EXPERIENCE * 0.9  # 18.0 / 20.0
            base_reason = f"Candidate has {candidate_years:.1f} yrs vs {required_years:.1f} yrs required (slight overqualification factor)"
        else:
            base_score = WEIGHT_EXPERIENCE
            base_reason = f"Candidate meets or exceeds experience: {candidate_years:.1f} yrs vs {required_years:.1f} yrs required"
    else:
        ratio = max(0.0, candidate_years / required_years)
        base_score = round(ratio * WEIGHT_EXPERIENCE, 1)
        shortfall = round(WEIGHT_EXPERIENCE - base_score, 1)
        base_reason = f"Experience shortfall: {candidate_years:.1f} yrs vs {required_years:.1f} yrs required (-{shortfall:.1f} pts)"

    # Calculate blended ratio between core skills and required skills
    if num_core_skills > 0:
        blended_ratio = 0.6 * core_match_ratio + 0.4 * req_match_ratio
    else:
        blended_ratio = req_match_ratio

    if num_required_skills > 0 or num_core_skills > 0:
        skill_factor = max(0.25, min(1.0, blended_ratio))
        final_score = round(base_score * skill_factor, 1)
        if skill_factor < 1.0:
            if num_core_skills > 0:
                reason = (
                    f"Experience discounted: core skills {core_matched_count}/{num_core_skills}, "
                    f"required skills {req_matched_count}/{num_required_skills} "
                    f"({final_score:.1f}/{WEIGHT_EXPERIENCE:.0f} pts)"
                )
            else:
                reason = (
                    f"Experience discounted: only {req_matched_count}/{num_required_skills} required skills present "
                    f"({final_score:.1f}/{WEIGHT_EXPERIENCE:.0f} pts)"
                )
        else:
            reason = f"{base_reason} ({final_score:.1f}/{WEIGHT_EXPERIENCE:.0f} pts)"
    else:
        final_score = round(base_score, 1)
        reason = f"{base_reason} ({final_score:.1f}/{WEIGHT_EXPERIENCE:.0f} pts)"

    return final_score, reason


def evaluate_education(
    jd_education: List[str],
    candidate_education: List[Dict[str, Any]],
) -> Tuple[float, str]:
    """
    Compares candidate education credentials with JD requirements.
    """
    if not candidate_education:
        # Candidate has no education listed
        score = 2.0
        reason = f"No verified higher education detected on resume ({score:.1f}/{WEIGHT_EDUCATION:.0f} pts)"
        return score, reason

    cand_degrees = [item.get("degree", "").lower() for item in candidate_education if item.get("degree")]
    cand_degrees_str = " ".join(cand_degrees)

    if not jd_education:
        # No strict degree specified by JD, candidate has degree
        score = WEIGHT_EDUCATION
        deg_label = candidate_education[0].get("degree", "Degree")
        return score, f"Candidate holds recognized higher education: {deg_label} ({score:.1f}/{WEIGHT_EDUCATION:.0f} pts)"

    # JD requires specific degrees
    has_bachelors = any(d in cand_degrees_str for d in ["b.tech", "b.e", "b.s", "bachelor", "bca", "bba"])
    has_masters = any(d in cand_degrees_str for d in ["m.tech", "m.e", "m.s", "master", "mca", "mba"])
    has_phd = any(d in cand_degrees_str for d in ["phd", "doctorate"])

    jd_text = " ".join(jd_education).lower()

    if ("phd" in jd_text or "doctorate" in jd_text) and not has_phd:
        score = 5.0
        return score, f"JD desires PhD/Doctorate, candidate has Bachelor's/Master's ({score:.1f}/{WEIGHT_EDUCATION:.0f} pts)"

    if ("master" in jd_text or "m.tech" in jd_text) and not (has_masters or has_phd):
        score = 7.0
        return score, f"JD desires Master's degree, candidate has Bachelor's ({score:.1f}/{WEIGHT_EDUCATION:.0f} pts)"

    # Candidate has suitable or higher qualification
    score = WEIGHT_EDUCATION
    return score, f"Candidate education meets required criteria ({score:.1f}/{WEIGHT_EDUCATION:.0f} pts)"


def evaluate_relevance(
    certifications: List[str],
    projects: List[Dict[str, Any]],
) -> Tuple[float, str]:
    """
    Scores additional candidate relevance indicators (portfolio projects & industry certifications).
    """
    num_certs = len(certifications)
    num_projects = len(projects)

    if num_certs > 0 and num_projects > 0:
        score = WEIGHT_RELEVANCE
        reason = f"Verified {num_projects} portfolio projects and {num_certs} certifications ({score:.1f}/{WEIGHT_RELEVANCE:.0f} pts)"
    elif num_projects > 0:
        score = 3.5
        reason = f"Verified {num_projects} portfolio projects ({score:.1f}/{WEIGHT_RELEVANCE:.0f} pts)"
    elif num_certs > 0:
        score = 3.0
        reason = f"Verified {num_certs} industry certifications ({score:.1f}/{WEIGHT_RELEVANCE:.0f} pts)"
    else:
        score = 1.0
        reason = f"No explicit project portfolio or certifications listed ({score:.1f}/{WEIGHT_RELEVANCE:.0f} pts)"

    return score, reason


def calculate_match(
    jd_title: str,
    jd_raw_text: str,
    jd_required_skills: List[str],
    jd_preferred_skills: List[str],
    jd_min_experience: float,
    jd_education: List[str],
    resume_raw_text: str,
    resume_skills: List[str],
    resume_experience_years: float,
    resume_education: List[Dict[str, Any]],
    resume_certifications: List[str],
    resume_projects: List[Dict[str, Any]],
    jd_core_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Main matching engine evaluating a single resume against a job description.
    Produces an explainable breakdown totaling 100 points.
    """
    reasons: List[str] = []

    # If core skills not explicitly provided, extract them dynamically
    if jd_core_skills is None:
        from app.services.jd_service import extract_core_skills
        effective_core_skills = extract_core_skills(jd_title, jd_raw_text, jd_required_skills)
    else:
        effective_core_skills = jd_core_skills

    # 1. Skill evaluation (40%)
    skill_score, matched_skills, partial_skills, missing_skills, skill_reasons = evaluate_skills(
        required_skills=jd_required_skills,
        preferred_skills=jd_preferred_skills,
        candidate_skills=resume_skills,
        core_skills=effective_core_skills,
    )
    reasons.extend(skill_reasons)

    # 2. Semantic text similarity (25%)
    raw_semantic_sim = compute_text_similarity(jd_raw_text, resume_raw_text)
    calibrated_sim = calibrate_semantic_similarity(raw_semantic_sim)
    semantic_score = round(calibrated_sim * WEIGHT_SEMANTIC, 1)
    reasons.append(
        f"Document semantic similarity: {raw_semantic_sim*100:.1f}% "
        f"(calibrated to {semantic_score:.1f}/{WEIGHT_SEMANTIC:.0f} pts)"
    )

    # 3. Experience evaluation (20%)
    num_req = len(jd_required_skills)
    req_matched = [s for s in matched_skills if s in jd_required_skills]
    req_partial = [s for s in partial_skills if any(s.startswith(f"{r} (~") for r in jd_required_skills)]
    req_match_ratio = (len(req_matched) + 0.5 * len(req_partial)) / num_req if num_req > 0 else 1.0

    core_skills_list = effective_core_skills or []
    num_core = len(core_skills_list)
    core_matched = [s for s in core_skills_list if s in matched_skills]
    core_partial = [s for s in core_skills_list if any(p.startswith(f"{s} (~") for p in partial_skills)]
    core_match_ratio = (len(core_matched) + 0.5 * len(core_partial)) / num_core if num_core > 0 else 1.0

    exp_score, exp_reason = evaluate_experience(
        candidate_years=resume_experience_years,
        required_years=jd_min_experience,
        req_matched_count=len(req_matched),
        num_required_skills=num_req,
        req_match_ratio=req_match_ratio,
        core_matched_count=len(core_matched),
        num_core_skills=num_core,
        core_match_ratio=core_match_ratio,
    )
    reasons.append(exp_reason)

    # 4. Education evaluation (10%)
    edu_score, edu_reason = evaluate_education(
        jd_education=jd_education,
        candidate_education=resume_education,
    )
    reasons.append(edu_reason)

    # 5. Certifications & projects relevance (5%)
    rel_score, rel_reason = evaluate_relevance(
        certifications=resume_certifications,
        projects=resume_projects,
    )
    reasons.append(rel_reason)

    # Overall composite score (0 - 100)
    raw_total = skill_score + semantic_score + exp_score + edu_score + rel_score
    overall_score = round(max(0.0, min(100.0, raw_total)), 1)

    # 6. Core-skill gate:
    # If core skills exist and candidate matches NONE of them (exact or partial),
    # cap overall score at CORE_SKILL_GATE_CAP (30.0). If candidate matches some but not all, no cap.
    if effective_core_skills:
        matched_core = [
            s for s in effective_core_skills
            if s in matched_skills or any(p.startswith(f"{s} (~") for p in partial_skills)
        ]
        if len(matched_core) == 0:
            if overall_score > CORE_SKILL_GATE_CAP:
                overall_score = CORE_SKILL_GATE_CAP
            reasons.append(
                f"Capped: none of the core skills ({', '.join(effective_core_skills)}) found"
            )

    score_breakdown = {
        "skills": {"score": skill_score, "max": WEIGHT_SKILLS},
        "semantic": {"score": semantic_score, "max": WEIGHT_SEMANTIC},
        "experience": {"score": exp_score, "max": WEIGHT_EXPERIENCE},
        "education": {"score": edu_score, "max": WEIGHT_EDUCATION},
        "relevance": {"score": rel_score, "max": WEIGHT_RELEVANCE},
    }

    return {
        "overall_score": overall_score,
        "score_breakdown": score_breakdown,
        "matched_skills": matched_skills,
        "partially_matched_skills": partial_skills,
        "missing_skills": missing_skills,
        "reasons": reasons,
    }
