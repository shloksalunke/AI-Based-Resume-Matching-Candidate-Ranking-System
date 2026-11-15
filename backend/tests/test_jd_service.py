import pytest
from app.services.jd_service import (
    split_jd_sections,
    extract_min_experience,
    parse_job_description,
)


def test_jd_section_heading_with_slash_and_ampersand():
    jd_text = """
    Job Title: Senior Java Developer

    Requirements / Must Have:
    - Java
    - Spring Boot
    - PostgreSQL

    Nice to Have / Preferred Qualifications:
    - Docker
    - Kubernetes
    """
    gen, req, pref = split_jd_sections(jd_text)
    assert "Java" in req
    assert "Spring Boot" in req
    assert "Docker" in pref
    assert "Kubernetes" in pref

    parsed = parse_job_description(jd_text)
    assert "Java" in parsed["required_skills"]
    assert "Spring Boot" in parsed["required_skills"]
    assert "Docker" in parsed["preferred_skills"]
    assert "Kubernetes" in parsed["preferred_skills"]


def test_extract_min_experience_patterns():
    # 1. Experience Level: 3+ years
    text_level = "Experience Level: 3+ years in software engineering"
    assert extract_min_experience(text_level) == 3.0

    # 2. 3+ years
    text_plus = "Must possess 3+ years working in backend microservices"
    assert extract_min_experience(text_plus) == 3.0

    # 3. minimum 3 years
    text_min = "Minimum 3 years of hands-on Java development"
    assert extract_min_experience(text_min) == 3.0

    # 4. at least 3 years
    text_least = "At least 3 years building cloud solutions"
    assert extract_min_experience(text_least) == 3.0

    # 5. 3-5 years (take the minimum)
    text_range = "Looking for an engineer with 3-5 years of industry experience"
    assert extract_min_experience(text_range) == 3.0


def test_core_skills_extraction_sample_jd():
    sample_jd = """
    Job Title: Java Spring Boot Developer
    Location: Remote
    Experience Level: 3+ years

    About the Role:
    We are looking for a Java Spring Boot Developer to develop backend microservices in Java.

    Requirements / Must Have:
    - 3+ years of experience with Java and Spring Boot framework
    - Experience with PostgreSQL or MySQL
    - Docker containerization and Git
    - Bachelor's degree in Computer Science

    Nice to Have:
    - AWS or Kubernetes
    """
    parsed = parse_job_description(sample_jd, title="Java Spring Boot Developer")
    assert "core_skills" in parsed
    # Both Java and Spring Boot must be identified as core skills
    assert "Java" in parsed["core_skills"]
    assert "Spring Boot" in parsed["core_skills"]
    assert len(parsed["core_skills"]) >= 2

