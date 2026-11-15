import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, Optional

from app.core.config import settings
from app.schemas.llm import CandidateAiSummary, CandidateAiEvaluation

logger = logging.getLogger(__name__)


def is_llm_enabled() -> bool:
    """
    Returns True if LLM feature flag is active and an API key is provided.
    """
    return bool(settings.USE_LLM and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())


def _build_evaluation_prompt(
    jd_requirements: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    standard_result: Dict[str, Any],
) -> str:
    """
    Builds a concise prompt containing only structured parsed fields and explainability metrics.
    Explicitly omits full raw resume text to minimize tokens and prevent hallucination.
    """
    jd_title = jd_requirements.get("title", "Target Role")
    jd_min_exp = jd_requirements.get("min_experience", 0.0)
    jd_core_skills = jd_requirements.get("core_skills", [])
    jd_req_skills = jd_requirements.get("required_skills", [])
    jd_pref_skills = jd_requirements.get("preferred_skills", [])
    jd_edu = jd_requirements.get("education", [])
    jd_edu_str = ", ".join(jd_edu) if jd_edu else "Any relevant degree"

    name = candidate_profile.get("name") or candidate_profile.get("filename", "Candidate")
    exp_years = candidate_profile.get("total_experience_years", 0.0)
    skills = candidate_profile.get("skills", [])
    edu_list = candidate_profile.get("education", [])
    edu_str = ", ".join([e.get("degree", "") for e in edu_list if isinstance(e, dict) and e.get("degree")]) or "None specified"

    overall_score = standard_result.get("overall_score", 0.0)
    matched_skills = standard_result.get("matched_skills", [])
    partial_skills = standard_result.get("partially_matched_skills", [])
    missing_skills = standard_result.get("missing_skills", [])
    reasons = standard_result.get("reasons", [])

    return f"""You are an expert technical interviewer and recruitment evaluator. Evaluate the candidate against the job description based strictly on the facts below.

JOB REQUIREMENTS:
- Role Title: {jd_title}
- Minimum Required Experience: {jd_min_exp} years
- Core Skills (Crucial Priority): {', '.join(jd_core_skills) if jd_core_skills else 'None'}
- Required Skills: {', '.join(jd_req_skills) if jd_req_skills else 'None'}
- Preferred / Nice-to-Have Skills: {', '.join(jd_pref_skills) if jd_pref_skills else 'None'}
- Education Requirement: {jd_edu_str}

CANDIDATE PROFILE:
- Name: {name}
- Total Experience: {exp_years:.1f} years
- Candidate Skills: {', '.join(skills[:30])}
- Education: {edu_str}

STANDARD MATCHING ENGINE FINDINGS:
- Baseline Deterministic Score: {overall_score:.1f} / 100
- Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}
- Partial / Semantic Matches: {', '.join(partial_skills) if partial_skills else 'None'}
- Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}
- Engine Notes:
{chr(10).join(f'  * {r}' for r in reasons)}

INSTRUCTIONS:
1. Ground your judgment strictly in the facts provided above. NEVER invent or assume skills, tools, or experience not explicitly listed.
2. Judge against the JD's core skills first. If the candidate lacks core skills (e.g. applying for a Java role with only Python experience), penalize the score heavily.
3. Return a STRICT JSON object with these EXACT keys:
   - "ai_score": A calibrated integer or float from 0 to 100 representing the candidate's holistic suitability.
   - "matched_skills": Array of strings of skills that match the JD requirements.
   - "missing_skills": Array of strings of important JD skills missing from candidate.
   - "equivalent_skills": Array of strings in format "JD skill ~ candidate skill" representing transferable technologies.
   - "experience_assessment": A concise assessment of candidate's total years and seniority relevance against the required {jd_min_exp} years.
   - "summary": A concise 2-3 sentence executive summary of candidate alignment.
   - "strengths": Array of at most 3 specific bullet points highlighting key advantages.
   - "concerns": Array of at most 3 specific bullet points highlighting gaps or risks.
   - "recommendation": Exactly one of "Strong fit", "Possible fit", or "Weak fit".
   - "reasons": Array of at most 5 bullet points explaining the rationale behind the ai_score.

4. Output valid JSON only, without any markdown formatting or surrounding commentary.
"""


def _clean_json_output(raw_text: str) -> str:
    """Strips markdown fences or backticks from LLM output."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def evaluate_candidate(
    jd_requirements: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    standard_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluates a candidate using Gemini with temperature=0 and a compact prompt.
    Returns a validated dictionary adhering to CandidateAiEvaluation schema.
    Never raises exceptions; returns a dict containing an 'error' key on failure.
    Retries once on transient errors.
    """
    if not is_llm_enabled():
        return {"error": "LLM service is disabled or GEMINI_API_KEY is missing."}

    def _call_gemini_eval() -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = _build_evaluation_prompt(jd_requirements, candidate_profile, standard_result)
        config = types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=1000,
            response_mime_type="application/json",
        )

        # Retry once on transient errors
        attempts = 2
        last_exc = None
        for attempt in range(attempts):
            try:
                response = client.models.generate_content(
                    model=settings.LLM_MODEL,
                    contents=prompt,
                    config=config,
                )
                return response.text or ""
            except Exception as exc:
                last_exc = exc
                if attempt < attempts - 1:
                    time.sleep(0.5)
                    continue
                raise last_exc
        return ""

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_gemini_eval)
            raw_output = future.result(timeout=settings.LLM_TIMEOUT_SECONDS)

        cleaned = _clean_json_output(raw_output)
        data = json.loads(cleaned)
        validated = CandidateAiEvaluation.model_validate(data)
        return validated.model_dump()

    except FuturesTimeoutError:
        logger.warning(f"LLM candidate evaluation timed out after {settings.LLM_TIMEOUT_SECONDS}s")
        return {"error": f"LLM evaluation timed out after {settings.LLM_TIMEOUT_SECONDS}s"}
    except json.JSONDecodeError as exc:
        logger.warning(f"Failed to parse LLM evaluation response as JSON: {exc}")
        return {"error": f"Malformed LLM output: {exc}"}
    except Exception as exc:
        logger.warning(f"Error during LLM candidate evaluation: {exc}")
        return {"error": f"LLM evaluation failed: {exc}"}


def generate_candidate_summary(
    candidate_profile: Dict[str, Any],
    jd_requirements: Dict[str, Any],
    score_result: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Backward-compatible wrapper reusing evaluate_candidate.
    Returns a dictionary matching CandidateAiSummary or None if disabled/failed.
    """
    eval_result = evaluate_candidate(jd_requirements, candidate_profile, score_result)
    if not eval_result or eval_result.get("error"):
        return None

    try:
        summary_obj = CandidateAiSummary(
            summary=eval_result.get("summary", ""),
            strengths=eval_result.get("strengths", []),
            concerns=eval_result.get("concerns", []),
            recommendation=eval_result.get("recommendation", "Possible fit"),
        )
        return summary_obj.model_dump()
    except Exception as exc:
        logger.warning(f"Error mapping AI evaluation to summary: {exc}")
        return None
