import pytest
from app.services.parser_service import (
    extract_email,
    extract_phone,
    extract_skills,
    extract_total_experience_years,
    extract_education,
    parse_resume_content,
)


def test_extract_email():
    text = "Candidate can be reached at john.doe@example.org or personal@gmail.com"
    email = extract_email(text)
    assert email == "john.doe@example.org"


def test_extract_phone():
    samples = [
        "Call me at +1 (555) 123-4567 for any queries.",
        "Mobile: 9876543210 available anytime.",
        "Tel: 555-234-5678",
    ]
    for sample in samples:
        phone = extract_phone(sample)
        assert phone is not None
        # Must have at least 10 digits
        assert len([c for c in phone if c.isdigit()]) >= 10


def test_skill_alias_extraction():
    text = """
    Technical Background:
    Proficient in JS, TS, py, k8s, docker, and postgresql.
    Experience with ReactJS, node.js, AWS, and git.
    """
    skills = extract_skills(text)
    # Ensure aliases map to canonical skill names
    assert "JavaScript" in skills
    assert "TypeScript" in skills
    assert "Python" in skills
    assert "Kubernetes" in skills
    assert "Docker" in skills
    assert "PostgreSQL" in skills
    assert "React" in skills
    assert "Node.js" in skills
    assert "AWS" in skills
    assert "Git" in skills


def test_experience_from_phrase():
    text = "Senior Software Engineer with 5+ years of experience leading cross-functional teams."
    years = extract_total_experience_years(text)
    assert years >= 5.0


def test_experience_from_date_ranges():
    text = """
    Work Experience:
    Senior Software Engineer | Jan 2020 - Present
    Developed microservices in Python.
    
    Software Developer | Jan 2018 - Dec 2019
    Built React web applications.
    """
    years = extract_total_experience_years(text)
    # From 2018 to now is at least 6 years
    assert years >= 6.0


def test_education_detection():
    text = """
    Education:
    B.Tech in Computer Science and Engineering, 2020
    National Institute of Technology
    """
    edu = extract_education(text)
    assert len(edu) >= 1
    degree_names = [e["degree"].lower() for e in edu]
    assert any("b.tech" in d or "bachelor" in d for d in degree_names)


def test_parse_resume_content_integrated():
    sample_resume = """
    Alice Walker
    alice.walker@email.com
    (555) 987-6543
    New York, NY

    Professional Summary:
    Full Stack Developer with 4 years of experience building modern web applications.
    
    Skills:
    Python, React, TypeScript, Docker, PostgreSQL, REST APIs

    Experience:
    Software Engineer - TechCorp
    Mar 2021 - Present
    - Built scalable backend microservices with FastAPI and PostgreSQL.
    - Designed interactive frontend dashboards with React and TypeScript.

    Junior Developer - StartupHub
    Jan 2020 - Feb 2021
    - Developed web interfaces.

    Education:
    Bachelor of Science in Computer Science, 2019
    State University

    Certifications:
    AWS Certified Solutions Architect
    """
    parsed = parse_resume_content("alice_resume.pdf", sample_resume)
    assert parsed["name"] is not None
    assert parsed["email"] == "alice.walker@email.com"
    assert parsed["phone"] is not None
    assert "Python" in parsed["skills"]
    assert "React" in parsed["skills"]
    assert "TypeScript" in parsed["skills"]
    assert parsed["total_experience_years"] >= 4.0
    assert len(parsed["education"]) >= 1
    assert any("AWS Certified" in c for c in parsed["certifications"])


def test_extract_name_failing_formats_and_newlines():
    from app.services.parser_service import extract_name

    # Case A: Two lines where first line has title and second has 'Professional', but email is aarav.sharma@fakemail.net
    text_a = """
    Java Spring Boot Engineer
    Professional
    aarav.sharma@fakemail.net | +91 98201 12345
    Summary of qualifications.
    """
    name_a = extract_name(text_a)
    assert name_a is not None
    assert "\n" not in name_a
    assert "Engineer" not in name_a
    assert "Professional" not in name_a
    assert name_a == "Aarav Sharma"

    # Case B: First line name, second line email
    text_b = """
    Aditya Joshi
    aditya.joshi@campusgrad.edu
    +91 97123 45678
    Summary: Recent graduate.
    """
    name_b = extract_name(text_b)
    assert name_b == "Aditya Joshi"
    assert "\n" not in name_b
    assert "@" not in name_b


def test_fresher_education_dates_not_counted_as_experience():
    fresher_resume = """
    Pooja Reddy
    pooja.reddy@studentmail.ac.in | +91 98855 66778
    Summary:
    Motivated fresher with a Bachelor's degree in Computer Science. Seeking an entry-level development role.

    Education:
    B.Tech in Computer Science (2020 - 2024)
    Hyderabad Institute of Technology
    CGPA: 8.5

    Skills:
    Java, Python, SQL, HTML, CSS, Git

    Projects:
    Student Portal: Full stack web app
    """
    parsed = parse_resume_content("pooja_fresher.pdf", fresher_resume)
    assert parsed["total_experience_years"] == 0.0
    assert len(parsed["education"]) >= 1
    assert parsed["education"][0]["degree"] in ["B.Tech", "Bachelor's"]
    assert "Hyderabad Institute of Technology" in parsed["education"][0]["institution"]


def test_internship_and_company_extraction():
    resume_with_intern = """
    Shlok Sharma
    shlok@gmail.com | +91 9876543210
    Summary:
    Fresher seeking software developer opportunities.

    Education:
    B.Tech in Computer Science (2020 - 2024)
    MIT Academy of Engineering

    Experience:
    Web Development Intern at CodeClause
    Jan 2024 - Mar 2024
    - Built responsive frontend using React.
    - Implemented REST API services.
    """
    parsed = parse_resume_content("shlok_resume.pdf", resume_with_intern)
    # 3 months internship is ~0.2 years, not 4.0 years!
    assert 0.1 <= parsed["total_experience_years"] <= 0.5
    assert len(parsed["companies_and_designations"]) >= 1
    role = parsed["companies_and_designations"][0]
    assert "Intern" in role["designation"] or "Developer" in role["designation"]
    assert "CodeClause" in role["company"]
    assert len(parsed["education"]) >= 1
    assert "MIT Academy of Engineering" in parsed["education"][0]["institution"]


def test_single_month_experience_is_not_one_year():
    single_month_resume = """
    Priya Nair
    priya@example.com | +91 91234 56789

    Education:
    B.Tech in Information Technology
    2020 - 2024
    Anna University

    Experience:
    Frontend Intern at WebSolutions
    April 2025
    - Developed landing pages using React and Tailwind CSS.
    """
    parsed = parse_resume_content("priya_resume.pdf", single_month_resume)
    # Must be 1 month (~0.08 - 0.1 yrs), definitely not 1.0 year!
    assert 0.05 <= parsed["total_experience_years"] <= 0.2
    assert parsed["total_experience_years"] < 0.5
    assert len(parsed["companies_and_designations"]) >= 1
    assert "WebSolutions" in parsed["companies_and_designations"][0]["company"]

