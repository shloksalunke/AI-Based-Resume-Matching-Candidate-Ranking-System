import pytest
from app.services.matching_service import calculate_match


@pytest.fixture
def sample_job():
    return {
        "title": "Senior Python Backend Engineer",
        "raw_text": """
        Senior Python Backend Engineer
        About the role:
        We are seeking a Senior Backend Engineer to architect scalable services.
        
        Requirements:
        - 5+ years of software development experience
        - Strong proficiency in Python, FastAPI, PostgreSQL, and Docker
        - Experience with AWS and REST APIs
        - Bachelor's degree in Computer Science or equivalent
        
        Nice to have:
        - Redis, Kubernetes, CI/CD
        """,
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "REST APIs"],
        "preferred_skills": ["Redis", "Kubernetes", "CI/CD"],
        "min_experience": 5.0,
        "education": ["Bachelor's", "Computer Science"],
    }


def test_strong_match_scores_higher_than_weak_match(sample_job):
    # Strong candidate: has all required skills, preferred skills, 6 years exp, degree, certs
    strong_candidate = {
        "raw_text": """
        Senior Backend Engineer with 6 years of experience building Python and FastAPI microservices.
        Deep knowledge of PostgreSQL database optimization, Docker containerization, and AWS cloud architecture.
        Hands-on with Redis caching and Kubernetes clusters.
        Bachelor of Science in Computer Science.
        AWS Certified Developer.
        """,
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "REST APIs", "Redis", "Kubernetes"],
        "experience": 6.0,
        "education": [{"degree": "Bachelor of Science in Computer Science"}],
        "certifications": ["AWS Certified Developer"],
        "projects": [{"title": "Cloud Microservices", "description": "Scaled API to 10k RPS"}],
    }

    # Weak candidate: only 1 skill, 1 year exp, unrelated background
    weak_candidate = {
        "raw_text": """
        Junior Web Designer with 1 year of experience creating HTML email templates and basic graphics.
        Minimal exposure to Python scripts.
        Associate degree in Art.
        """,
        "skills": ["HTML5", "CSS3", "Python"],
        "experience": 1.0,
        "education": [{"degree": "Associate degree"}],
        "certifications": [],
        "projects": [],
    }

    strong_result = calculate_match(
        jd_title=sample_job["title"],
        jd_raw_text=sample_job["raw_text"],
        jd_required_skills=sample_job["required_skills"],
        jd_preferred_skills=sample_job["preferred_skills"],
        jd_min_experience=sample_job["min_experience"],
        jd_education=sample_job["education"],
        resume_raw_text=strong_candidate["raw_text"],
        resume_skills=strong_candidate["skills"],
        resume_experience_years=strong_candidate["experience"],
        resume_education=strong_candidate["education"],
        resume_certifications=strong_candidate["certifications"],
        resume_projects=strong_candidate["projects"],
    )

    weak_result = calculate_match(
        jd_title=sample_job["title"],
        jd_raw_text=sample_job["raw_text"],
        jd_required_skills=sample_job["required_skills"],
        jd_preferred_skills=sample_job["preferred_skills"],
        jd_min_experience=sample_job["min_experience"],
        jd_education=sample_job["education"],
        resume_raw_text=weak_candidate["raw_text"],
        resume_skills=weak_candidate["skills"],
        resume_experience_years=weak_candidate["experience"],
        resume_education=weak_candidate["education"],
        resume_certifications=weak_candidate["certifications"],
        resume_projects=weak_candidate["projects"],
    )

    assert strong_result["overall_score"] > weak_result["overall_score"]
    assert strong_result["overall_score"] >= 80.0
    assert weak_result["overall_score"] < 50.0


def test_missing_required_skill_lowers_score(sample_job):
    full_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "REST APIs"]
    partial_skills = ["Python", "FastAPI"]  # missing 4 required skills

    result_full = calculate_match(
        jd_title=sample_job["title"],
        jd_raw_text=sample_job["raw_text"],
        jd_required_skills=sample_job["required_skills"],
        jd_preferred_skills=sample_job["preferred_skills"],
        jd_min_experience=sample_job["min_experience"],
        jd_education=sample_job["education"],
        resume_raw_text=sample_job["raw_text"],
        resume_skills=full_skills,
        resume_experience_years=5.0,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[],
    )

    result_missing = calculate_match(
        jd_title=sample_job["title"],
        jd_raw_text=sample_job["raw_text"],
        jd_required_skills=sample_job["required_skills"],
        jd_preferred_skills=sample_job["preferred_skills"],
        jd_min_experience=sample_job["min_experience"],
        jd_education=sample_job["education"],
        resume_raw_text=sample_job["raw_text"],
        resume_skills=partial_skills,
        resume_experience_years=5.0,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[],
    )

    assert result_full["overall_score"] > result_missing["overall_score"]
    assert len(result_missing["missing_skills"]) >= 3
    assert result_full["score_breakdown"]["skills"]["score"] > result_missing["score_breakdown"]["skills"]["score"]


def test_experience_shortfall_penalty(sample_job):
    # Candidate with 2 years experience for 5 years required job
    short_candidate = calculate_match(
        jd_title=sample_job["title"],
        jd_raw_text=sample_job["raw_text"],
        jd_required_skills=sample_job["required_skills"],
        jd_preferred_skills=sample_job["preferred_skills"],
        jd_min_experience=sample_job["min_experience"],
        jd_education=sample_job["education"],
        resume_raw_text=sample_job["raw_text"],
        resume_skills=sample_job["required_skills"],
        resume_experience_years=2.0,  # 2 yrs vs 5 yrs
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[],
    )

    full_candidate = calculate_match(
        jd_title=sample_job["title"],
        jd_raw_text=sample_job["raw_text"],
        jd_required_skills=sample_job["required_skills"],
        jd_preferred_skills=sample_job["preferred_skills"],
        jd_min_experience=sample_job["min_experience"],
        jd_education=sample_job["education"],
        resume_raw_text=sample_job["raw_text"],
        resume_skills=sample_job["required_skills"],
        resume_experience_years=5.0,  # 5 yrs vs 5 yrs
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[],
    )

    assert full_candidate["score_breakdown"]["experience"]["score"] == 20.0
    # 2/5 * 20 = 8.0
    assert short_candidate["score_breakdown"]["experience"]["score"] == 8.0
    assert short_candidate["overall_score"] < full_candidate["overall_score"]
    assert any("shortfall" in r.lower() for r in short_candidate["reasons"])


def test_scores_always_within_0_to_100(sample_job):
    # Check extreme empty
    empty_result = calculate_match(
        jd_title=sample_job["title"],
        jd_raw_text=sample_job["raw_text"],
        jd_required_skills=sample_job["required_skills"],
        jd_preferred_skills=sample_job["preferred_skills"],
        jd_min_experience=sample_job["min_experience"],
        jd_education=sample_job["education"],
        resume_raw_text="",
        resume_skills=[],
        resume_experience_years=0.0,
        resume_education=[],
        resume_certifications=[],
        resume_projects=[],
    )

    # Check maximum candidate
    max_candidate = calculate_match(
        jd_title=sample_job["title"],
        jd_raw_text=sample_job["raw_text"],
        jd_required_skills=sample_job["required_skills"],
        jd_preferred_skills=sample_job["preferred_skills"],
        jd_min_experience=sample_job["min_experience"],
        jd_education=sample_job["education"],
        resume_raw_text=sample_job["raw_text"],
        resume_skills=sample_job["required_skills"] + sample_job["preferred_skills"],
        resume_experience_years=10.0,
        resume_education=[{"degree": "Master of Computer Science"}],
        resume_certifications=["AWS Certified", "PMP"],
        resume_projects=[{"title": "P1", "description": "D1"}],
    )

    assert 0.0 <= empty_result["overall_score"] <= 100.0
    assert 0.0 <= max_candidate["overall_score"] <= 100.0
    assert max_candidate["overall_score"] >= 95.0


def test_java_does_not_match_javascript_and_spring_boot_matches_spring_framework():
    """
    Verifies that false-positive pairs like Java and JavaScript never partially match,
    while valid same-category variants like Spring Boot and Spring Framework do partially match.
    """
    from app.services.matching_service import evaluate_skills

    # 1. Candidate has only JavaScript, but JD requires Java
    skill_score, matched, partial, missing, reasons = evaluate_skills(
        required_skills=["Java"],
        preferred_skills=[],
        candidate_skills=["JavaScript"],
    )
    # Java must NOT match or partially match JavaScript
    assert "Java" in missing
    assert "Java" not in matched
    assert not any("Java" in p for p in partial)
    assert skill_score == 0.0

    # 2. Candidate has Spring Framework, but JD requires Spring Boot
    sb_score, sb_matched, sb_partial, sb_missing, sb_reasons = evaluate_skills(
        required_skills=["Spring Boot"],
        preferred_skills=[],
        candidate_skills=["Spring Framework"],
    )
    # Spring Boot MUST partially match Spring Framework
    assert "Spring Boot" not in sb_missing
    assert any("Spring Boot (~ Spring Framework)" in p for p in sb_partial)
    assert sb_score > 0.0


def test_python_only_candidate_scores_below_java_spring_candidate():
    """
    Verifies that a senior Python-only developer (even with 7 years exp)
    scores substantially lower than a Java + Spring Boot developer for a Java role,
    due to missing core skills and experience score discounting.
    """
    java_jd = {
        "title": "Java Spring Boot Developer",
        "raw_text": "Looking for a Java Spring Boot Developer with 3+ years experience in Java, Spring Boot, PostgreSQL.",
        "required_skills": ["Java", "Spring Boot", "PostgreSQL"],
        "preferred_skills": ["Docker", "AWS"],
        "min_experience": 3.0,
        "education": ["B.Tech", "Computer Science"],
    }

    # Python candidate: 7 years experience, but strictly Python/Django/PostgreSQL/AWS
    python_candidate = calculate_match(
        jd_title=java_jd["title"],
        jd_raw_text=java_jd["raw_text"],
        jd_required_skills=java_jd["required_skills"],
        jd_preferred_skills=java_jd["preferred_skills"],
        jd_min_experience=java_jd["min_experience"],
        jd_education=java_jd["education"],
        resume_raw_text="Senior Python Developer with 7 years of experience in Python, Django, PostgreSQL, Docker, AWS.",
        resume_skills=["Python", "Django", "PostgreSQL", "Docker", "AWS"],
        resume_experience_years=7.0,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=["AWS Certified Developer"],
        resume_projects=[{"title": "Django API", "description": "High throughput service"}],
    )

    # Java candidate: 4 years experience, but has Java + Spring Boot + PostgreSQL
    java_candidate = calculate_match(
        jd_title=java_jd["title"],
        jd_raw_text=java_jd["raw_text"],
        jd_required_skills=java_jd["required_skills"],
        jd_preferred_skills=java_jd["preferred_skills"],
        jd_min_experience=java_jd["min_experience"],
        jd_education=java_jd["education"],
        resume_raw_text="Java Developer with 4 years of experience in Java, Spring Boot, PostgreSQL, Docker.",
        resume_skills=["Java", "Spring Boot", "PostgreSQL", "Docker"],
        resume_experience_years=4.0,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[{"title": "Spring Boot API", "description": "Microservices"}],
    )

    assert java_candidate["overall_score"] > python_candidate["overall_score"]
    # Python candidate experience should be discounted
    assert any("discounted" in r.lower() for r in python_candidate["reasons"])
    # Java candidate matches all 3 required skills
    assert len(java_candidate["matched_skills"]) >= 3
    # Python candidate has missing Java and Spring Boot
    assert "Java" in python_candidate["missing_skills"]
    assert "Spring Boot" in python_candidate["missing_skills"]


def test_python_only_scores_below_java_only_candidate_for_java_spring_jd():
    """
    (a) Python-only candidate scores below a Java-only candidate for a Java+Spring JD.
    Even if Python developer has more years of experience, lack of Java/Spring core skills
    and the core skill gate/weights ensure Java-only candidate ranks higher.
    """
    jd_title = "Java Spring Boot Developer"
    jd_text = "Looking for a Java Spring Boot Developer. Must have Java, Spring Boot, MySQL. 3+ years experience."
    req_skills = ["Java", "Spring Boot", "MySQL"]
    core_skills = ["Java", "Spring Boot"]

    # Java-only candidate (has Java, but no Python or other stack; 3.5 yrs)
    java_only = calculate_match(
        jd_title=jd_title,
        jd_raw_text=jd_text,
        jd_required_skills=req_skills,
        jd_preferred_skills=[],
        jd_min_experience=3.0,
        jd_education=["B.Tech"],
        resume_raw_text="Java Software Developer with 3.5 years of experience in Core Java and backend development.",
        resume_skills=["Java"],
        resume_experience_years=3.5,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[{"title": "Java Inventory System"}],
        jd_core_skills=core_skills,
    )

    # Python-only candidate (has Python, Django, PostgreSQL, Docker, Git; 7 yrs, but ZERO Java/Spring)
    python_only = calculate_match(
        jd_title=jd_title,
        jd_raw_text=jd_text,
        jd_required_skills=req_skills,
        jd_preferred_skills=[],
        jd_min_experience=3.0,
        jd_education=["B.Tech"],
        resume_raw_text="Senior Python Backend Developer with 7 years experience in Python, Django, PostgreSQL, Docker, Git.",
        resume_skills=["Python", "Django", "PostgreSQL", "Docker", "Git"],
        resume_experience_years=7.0,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[{"title": "Django API"}],
        jd_core_skills=core_skills,
    )

    assert java_only["overall_score"] > python_only["overall_score"]
    # Python-only candidate has matched none of the core skills
    assert any("Capped: none of the core skills" in r for r in python_only["reasons"])
    # Java-only matched 1 core skill, so cap should not apply
    assert not any("Capped: none of the core skills" in r for r in java_only["reasons"])


def test_core_skill_gate_cap_triggers_and_adds_reason():
    """
    (b) The core-skill gate cap triggers and adds a reason when a candidate
    matches none of the core skills.
    """
    jd_title = "Java Spring Boot Developer"
    jd_text = "Looking for a Java Spring Boot Developer with Java, Spring Boot, PostgreSQL, Docker."
    req_skills = ["Java", "Spring Boot", "PostgreSQL", "Docker"]
    core_skills = ["Java", "Spring Boot"]

    # Candidate with 10 years experience and auxiliary skills (PostgreSQL, Docker, Git, AWS), but NO core skills
    aux_candidate = calculate_match(
        jd_title=jd_title,
        jd_raw_text=jd_text,
        jd_required_skills=req_skills,
        jd_preferred_skills=["AWS", "Git"],
        jd_min_experience=3.0,
        jd_education=["B.Tech"],
        resume_raw_text="Senior DevOps Engineer with 10 years experience in PostgreSQL, Docker, AWS, Git, CI/CD, Kubernetes.",
        resume_skills=["PostgreSQL", "Docker", "AWS", "Git", "Kubernetes", "CI/CD"],
        resume_experience_years=10.0,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=["AWS Solution Architect"],
        resume_projects=[{"title": "Cloud Migration", "description": "Enterprise PostgreSQL & Docker infrastructure"}],
        jd_core_skills=core_skills,
    )

    # Score should be strictly capped at 30.0
    assert aux_candidate["overall_score"] <= 30.0
    # Must contain the exact capping reason
    cap_reasons = [r for r in aux_candidate["reasons"] if "Capped: none of the core skills (Java, Spring Boot) found" in r]
    assert len(cap_reasons) == 1


def test_candidate_with_all_core_skills_scores_higher_than_candidate_with_no_core_skills():
    """
    (3) A candidate matching all core skills but missing most other required skills
    must score higher than a candidate matching no core skills but many secondary skills.
    """
    jd_title = "Java Spring Boot Developer"
    jd_text = (
        "We are looking for a Java Spring Boot Developer. "
        "Requirements: Java, Spring Boot, PostgreSQL, Docker, Kubernetes, Kafka, Redis. "
        "Minimum 4 years of experience."
    )
    req_skills = ["Java", "Spring Boot", "PostgreSQL", "Docker", "Kubernetes", "Kafka", "Redis"]
    core_skills = ["Java", "Spring Boot"]

    # Candidate A: Matches ALL core skills (Java, Spring Boot), missing 5 other required skills
    candidate_a = calculate_match(
        jd_title=jd_title,
        jd_raw_text=jd_text,
        jd_required_skills=req_skills,
        jd_preferred_skills=[],
        jd_min_experience=4.0,
        jd_education=["B.Tech"],
        resume_raw_text="Java Developer with 5 years experience in Core Java and Spring Boot backend engineering.",
        resume_skills=["Java", "Spring Boot"],
        resume_experience_years=5.0,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[{"title": "Spring Microservice", "description": "Backend API"}],
        jd_core_skills=core_skills,
    )

    # Candidate B: Matches NO core skills, but matches 5 secondary required skills (PostgreSQL, Docker, Kubernetes, Kafka, Redis)
    candidate_b = calculate_match(
        jd_title=jd_title,
        jd_raw_text=jd_text,
        jd_required_skills=req_skills,
        jd_preferred_skills=[],
        jd_min_experience=4.0,
        jd_education=["B.Tech"],
        resume_raw_text="DevOps and Data Engineer with 5 years experience in PostgreSQL, Docker, Kubernetes, Kafka, Redis.",
        resume_skills=["PostgreSQL", "Docker", "Kubernetes", "Kafka", "Redis"],
        resume_experience_years=5.0,
        resume_education=[{"degree": "B.Tech"}],
        resume_certifications=[],
        resume_projects=[{"title": "Cloud Pipeline", "description": "Data processing"}],
        jd_core_skills=core_skills,
    )

    # Candidate A must score strictly higher than Candidate B
    assert candidate_a["overall_score"] > candidate_b["overall_score"]
    # Candidate B matched 0 core skills and must be capped at CORE_SKILL_GATE_CAP (30.0)
    assert candidate_b["overall_score"] <= 30.0
    assert any("Capped: none of the core skills" in r for r in candidate_b["reasons"])
    # Candidate A matched all core skills and experience discount shows core skills 2/2
    assert any("core skills 2/2" in r for r in candidate_a["reasons"])




