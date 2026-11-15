import os
from faker import Faker
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors
import docx

fake = Faker()

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data", "resumes")


CANDIDATE_DATA = [
    # 1. Strong Match 1 (PDF) - Aarav Sharma
    {
        "filename": "aarav_sharma_java_lead.pdf",
        "format": "pdf",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@fakemail.net",
        "phone": "+91 98201 12345",
        "title": "Senior Java Spring Boot Engineer",
        "summary": "Results-driven Backend Engineer with 5+ years of experience designing scalable microservices in Java and Spring Boot. Deep expertise in PostgreSQL database tuning, Docker, AWS cloud infrastructure, and distributed event architectures with Kafka and Redis.",
        "skills": "Java, Spring Boot, REST APIs, Microservices, PostgreSQL, Docker, Git, AWS, Kafka, Redis, JUnit, Agile / Scrum",
        "experience": [
            {
                "role": "Senior Software Engineer",
                "company": "FinTech Innovations Corp",
                "dates": "Jan 2019 - Present",
                "points": [
                    "Architected and deployed high-throughput Spring Boot microservices processing over 15,000 payment transactions per second.",
                    "Designed PostgreSQL database schemas with indexed query optimization, decreasing API latency by 45%.",
                    "Containerized 12 backend services using Docker and configured CI/CD deployment pipelines on AWS."
                ]
            },
            {
                "role": "Software Engineer",
                "company": "Infosys Technologies",
                "dates": "Jun 2017 - Dec 2018",
                "points": [
                    "Developed secure REST APIs using Java and Spring framework for enterprise banking portal.",
                    "Implemented comprehensive unit and integration test suites using JUnit and Mockito."
                ]
            }
        ],
        "education": "B.Tech in Computer Science and Engineering, 2017 - National Institute of Technology",
        "certifications": ["AWS Certified Solutions Architect - Associate", "Oracle Certified Java Professional"],
        "projects": [
            "Real-Time Payment Gateway: Resilient Spring Boot microservice handling multi-currency settlements with Redis caching.",
            "Event Notification Broker: Asynchronous event messaging system built with Kafka, Spring Boot, and PostgreSQL."
        ]
    },
    # 2. Strong Match 2 (DOCX) - Priya Patel
    {
        "filename": "priya_patel_spring_architect.docx",
        "format": "docx",
        "name": "Priya Patel",
        "email": "priya.patel@mockinbox.org",
        "phone": "+91 98450 67890",
        "title": "Lead Backend Engineer (Java / Spring)",
        "summary": "Accomplished Backend Developer with 6 years of experience building mission-critical distributed systems. Proficient in Java, Spring Boot, MySQL, Docker containerization, Kubernetes, and CI/CD automation.",
        "skills": "Java, Spring Boot, REST APIs, MySQL, Docker, Kubernetes, Git, CI/CD, Redis, Spring Framework, Agile / Scrum",
        "experience": [
            {
                "role": "Lead Backend Engineer",
                "company": "CloudMatrix Systems",
                "dates": "Mar 2018 - Present",
                "points": [
                    "Led a squad of 6 engineers developing enterprise microservices in Java and Spring Boot.",
                    "Managed MySQL clustering and automated schema migrations for 500k+ active daily users.",
                    "Implemented Docker container orchestration with Kubernetes and automated GitLab CI/CD pipelines."
                ]
            }
        ],
        "education": "B.Tech in Information Technology, 2018 - Delhi Technological University",
        "certifications": ["Certified Kubernetes Application Developer (CKAD)"],
        "projects": [
            "Order Fulfillment Platform: Scalable Spring Boot microservices with Redis session management and MySQL replication."
        ]
    },
    # 3. Strong Match 3 (PDF) - Rohan Verma
    {
        "filename": "rohan_verma_java_backend.pdf",
        "format": "pdf",
        "name": "Rohan Verma",
        "email": "rohan.verma@sampletalent.com",
        "phone": "+91 97110 54321",
        "title": "Backend Software Developer",
        "summary": "Backend developer with 4.5 years of industry experience creating robust REST APIs and database applications using Java, Spring Boot, PostgreSQL, and AWS.",
        "skills": "Java, Spring Boot, REST APIs, PostgreSQL, Docker, Git, AWS, Agile / Scrum",
        "experience": [
            {
                "role": "Software Developer",
                "company": "NeoSoft Solutions",
                "dates": "Jan 2020 - Present",
                "points": [
                    "Engineered cloud-native REST APIs using Java and Spring Boot.",
                    "Optimized complex PostgreSQL queries and maintained reliable Docker deployment images."
                ]
            },
            {
                "role": "Associate Developer",
                "company": "Wipro Tech",
                "dates": "Jul 2019 - Dec 2019",
                "points": [
                    "Maintained Java backend components and resolved defect tickets."
                ]
            }
        ],
        "education": "B.E. in Computer Engineering, 2019 - Pune University",
        "certifications": ["AWS Certified Developer - Associate"],
        "projects": [
            "Logistics Inventory REST API: Spring Boot application integrated with PostgreSQL and AWS S3."
        ]
    },
    # 4. Partial Match 1 (DOCX) - Vikram Malhotra (Core Java, NO Spring Boot)
    {
        "filename": "vikram_malhotra_core_java.docx",
        "format": "docx",
        "name": "Vikram Malhotra",
        "email": "vikram.malhotra@testmail.co",
        "phone": "+91 99200 98765",
        "title": "Java Systems Engineer",
        "summary": "Systems programmer with 4 years of hands-on experience in Core Java multi-threading, socket programming, MySQL, and Linux server environments. Strong foundation in object-oriented programming.",
        "skills": "Java, MySQL, REST APIs, Git, Linux Administration, Docker",
        "experience": [
            {
                "role": "Software Engineer",
                "company": "Zeta Trading Systems",
                "dates": "Jan 2020 - Present",
                "points": [
                    "Developed high-performance multithreaded order execution engines in Core Java.",
                    "Administered MySQL database tables and wrote stored procedures.",
                    "Configured Linux virtual machines and Docker containers for local simulation."
                ]
            }
        ],
        "education": "B.Tech in Computer Science, 2019 - Mumbai University",
        "certifications": [],
        "projects": [
            "High Speed Socket Server: Pure Java TCP communication server handling raw financial feeds."
        ]
    },
    # 5. Partial Match 2 (PDF) - Neha Kulkarni (Skills match, experience shortfall: 2 yrs vs 3 yrs)
    {
        "filename": "neha_kulkarni_junior_spring.pdf",
        "format": "pdf",
        "name": "Neha Kulkarni",
        "email": "neha.kulkarni@fakecareer.org",
        "phone": "+91 98900 11223",
        "title": "Junior Backend Developer",
        "summary": "Enthusiastic Backend Developer with 2 years of experience developing microservices using Java, Spring Boot, and PostgreSQL. Eager to expand technical knowledge in cloud systems.",
        "skills": "Java, Spring Boot, PostgreSQL, REST APIs, Git, Docker",
        "experience": [
            {
                "role": "Junior Backend Engineer",
                "company": "AlphaCode Labs",
                "dates": "Jan 2022 - Present",
                "points": [
                    "Built 5 CRUD REST APIs using Java and Spring Boot.",
                    "Wrote database migrations in PostgreSQL and packaged services with Docker."
                ]
            }
        ],
        "education": "B.Tech in Information Technology, 2021 - Pune University",
        "certifications": [],
        "projects": [
            "Customer Support Ticketing: Spring Boot microservice connected to PostgreSQL."
        ]
    },
    # 6. Partial Match 3 (DOCX) - Ananya Desai (Senior Backend, but Python/Django instead of Java)
    {
        "filename": "ananya_desai_python_backend.docx",
        "format": "docx",
        "name": "Ananya Desai",
        "email": "ananya.desai@sampleweb.in",
        "phone": "+91 97654 32109",
        "title": "Senior Backend Developer",
        "summary": "Senior backend developer with 5 years of experience architecting microservices, database storage, and cloud infrastructure using Python, Django, PostgreSQL, Docker, and AWS.",
        "skills": "Python, Django, FastAPI, PostgreSQL, Docker, AWS, Git, REST APIs, CI/CD",
        "experience": [
            {
                "role": "Senior Software Engineer",
                "company": "DataStream Analytics",
                "dates": "Jan 2019 - Present",
                "points": [
                    "Engineered distributed REST APIs in Python and Django with PostgreSQL.",
                    "Deployed containerized services to AWS EC2 using Docker and GitHub Actions."
                ]
            }
        ],
        "education": "B.Tech in Computer Science, 2018 - SRM University",
        "certifications": ["AWS Certified Developer"],
        "projects": [
            "Analytics Dashboard API: High-performance Python backend serving live telemetry."
        ]
    },
    # 7. Partial Match 4 (PDF) - Suresh Iyer (Java + Spring, missing DB & Docker)
    {
        "filename": "suresh_iyer_java_dev.pdf",
        "format": "pdf",
        "name": "Suresh Iyer",
        "email": "suresh.iyer@testprofile.net",
        "phone": "+91 98199 44556",
        "title": "Java Developer",
        "summary": "Java Developer with 3.5 years of experience writing web components and backend business logic using Java and Spring Boot.",
        "skills": "Java, Spring Boot, Git, Agile / Scrum",
        "experience": [
            {
                "role": "Software Developer",
                "company": "Apex Business Solutions",
                "dates": "Jun 2020 - Present",
                "points": [
                    "Maintained internal business services utilizing Java and Spring Boot.",
                    "Collaborated with QA teams in Agile sprint ceremonies."
                ]
            }
        ],
        "education": "B.Sc in Information Technology, 2020 - Mumbai University",
        "certifications": [],
        "projects": [
            "Internal Auditing Utility: Standalone Java application for generating audit reports."
        ]
    },
    # 8. Weak Match 1 (DOCX) - Kavita Rao (Frontend React/TypeScript only)
    {
        "filename": "kavita_rao_frontend_react.docx",
        "format": "docx",
        "name": "Kavita Rao",
        "email": "kavita.rao@webdesigners.org",
        "phone": "+91 98222 33445",
        "title": "Senior Frontend Developer",
        "summary": "Frontend Specialist with 4 years of experience crafting interactive single page applications using React, TypeScript, Tailwind CSS, Next.js, and Redux. Passionate about UI/UX accessibility.",
        "skills": "React, TypeScript, JavaScript, HTML5, CSS3, Tailwind CSS, Redux, Next.js, Git",
        "experience": [
            {
                "role": "Frontend Developer",
                "company": "PixelForge Studio",
                "dates": "Jan 2020 - Present",
                "points": [
                    "Architected responsive React web applications with TypeScript and Tailwind CSS.",
                    "Managed global application state using Redux Toolkit and React Query."
                ]
            }
        ],
        "education": "B.Tech in Electronics, 2019 - Bangalore University",
        "certifications": [],
        "projects": [
            "E-Commerce Storefront: Responsive React and Next.js customer checkout portal."
        ]
    },
    # 9. Weak Match 2 (PDF) - Manish Gupta (Data Analyst)
    {
        "filename": "manish_gupta_data_analyst.pdf",
        "format": "pdf",
        "name": "Manish Gupta",
        "email": "manish.gupta@analyticsdata.com",
        "phone": "+91 99300 77889",
        "title": "Business Intelligence & Data Analyst",
        "summary": "Data Analyst with 3 years of experience in data visualization, SQL queries, Tableau reporting, and Python data manipulation using Pandas and NumPy.",
        "skills": "Python, SQL, Tableau, Power BI, Pandas, NumPy, Data Analysis, Git",
        "experience": [
            {
                "role": "Data Analyst",
                "company": "InsightBI Solutions",
                "dates": "Jan 2021 - Present",
                "points": [
                    "Authored complex SQL queries to extract commercial KPIs from data warehouses.",
                    "Constructed interactive executive dashboards in Tableau and Power BI."
                ]
            }
        ],
        "education": "B.Sc in Statistics, 2020 - Delhi University",
        "certifications": ["Tableau Desktop Certified Associate"],
        "projects": [
            "Customer Churn Predictor: Exploratory data analysis in Python using Pandas."
        ]
    },
    # 10. Weak Match 3 (DOCX) - Divya Nair (QA Automation)
    {
        "filename": "divya_nair_qa_engineer.docx",
        "format": "docx",
        "name": "Divya Nair",
        "email": "divya.nair@qualitylab.net",
        "phone": "+91 98400 55667",
        "title": "QA Automation Engineer",
        "summary": "Quality Assurance Engineer with 2.5 years of experience in manual testing and automated test scripting using Selenium, Cypress, and JavaScript.",
        "skills": "Selenium, Cypress, JavaScript, Jira, Postman, Git",
        "experience": [
            {
                "role": "QA Test Engineer",
                "company": "TestLab Technologies",
                "dates": "Jun 2021 - Present",
                "points": [
                    "Authored automated regression test suites using Selenium WebDriver and Cypress.",
                    "Documented test plans, test cases, and bug reports in Jira."
                ]
            }
        ],
        "education": "B.Tech in Mechanical Engineering, 2021 - Calicut University",
        "certifications": ["ISTQB Foundation Level"],
        "projects": [
            "Cross-browser Test Automation: Automated test suite for web portal using Cypress."
        ]
    },
    # 11. Fresher 1 (PDF) - Aditya Joshi (Java/Spring Boot, 0.5 yrs internship)
    {
        "filename": "aditya_joshi_fresher_java.pdf",
        "format": "pdf",
        "name": "Aditya Joshi",
        "email": "aditya.joshi@campusgrad.edu",
        "phone": "+91 97123 45678",
        "title": "Recent Graduate / Associate Java Developer",
        "summary": "Recent Computer Science graduate with strong academic foundation in Java, Spring Boot, MySQL, and Docker. Completed a 6-month software engineering internship building REST APIs.",
        "skills": "Java, Spring Boot, REST APIs, MySQL, Docker, Git",
        "experience": [
            {
                "role": "Software Engineering Intern",
                "company": "TechStarts Accelerator",
                "dates": "Jun 2023 - Dec 2023",
                "points": [
                    "Assisted backend team in implementing Spring Boot REST endpoints.",
                    "Wrote unit tests and created Dockerfiles for local microservice testing."
                ]
            }
        ],
        "education": "B.Tech in Computer Science and Engineering, 2023 - National Institute of Technology",
        "certifications": [],
        "projects": [
            "Campus Placement Portal: End-to-end Spring Boot application with MySQL and JWT authentication.",
            "Library Management System: Java desktop tool using JDBC and MySQL."
        ]
    },
    # 12. Fresher 2 (PDF) - Pooja Reddy (Fresher, Core Java projects only, 0 yrs)
    {
        "filename": "pooja_reddy_fresher.pdf",
        "format": "pdf",
        "name": "Pooja Reddy",
        "email": "pooja.reddy@studentmail.ac.in",
        "phone": "+91 98855 66778",
        "title": "Computer Science Graduate",
        "summary": "Motivated fresher with a Bachelor's degree in Computer Science. Proficient in Java fundamentals, basic SQL databases, HTML5, and Git. Seeking an entry-level development role.",
        "skills": "Java, SQL, HTML5, CSS3, Git",
        "experience": [],
        "education": "B.Tech in Computer Science, 2024 - Hyderabad Institute of Technology",
        "certifications": [],
        "projects": [
            "Student Attendance Management: Core Java console application with MySQL persistence.",
            "Portfolio Website: Personal website built with HTML5 and CSS3."
        ]
    }
]


def create_pdf_resume(data: dict, filepath: str):
    """Generates a professional single/two-page PDF resume using ReportLab Platypus."""
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
    )
    subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
    )
    bullet_style = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        leftIndent=15,
        textColor=colors.HexColor("#2D3748"),
    )

    story = []

    # Header: Name, Contact info
    story.append(Paragraph(data["name"], title_style))
    contact_line = f"{data['email']} &nbsp;|&nbsp; {data['phone']} &nbsp;|&nbsp; {data.get('title', '')}"
    story.append(Paragraph(contact_line, subtitle_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceBefore=2, spaceAfter=8))

    # Professional Summary
    story.append(Paragraph("Professional Summary", section_heading))
    story.append(Paragraph(data["summary"], body_style))
    story.append(Spacer(1, 6))

    # Technical Skills
    story.append(Paragraph("Technical Skills", section_heading))
    story.append(Paragraph(data["skills"], body_style))
    story.append(Spacer(1, 6))

    # Experience
    story.append(Paragraph("Work Experience", section_heading))
    if data["experience"]:
        for exp in data["experience"]:
            role_header = f"<b>{exp['role']}</b> &nbsp;—&nbsp; {exp['company']} <i>({exp['dates']})</i>"
            story.append(Paragraph(role_header, body_style))
            for pt in exp["points"]:
                story.append(Paragraph(f"• {pt}", bullet_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Fresher seeking entry-level software engineering opportunities.", body_style))
        story.append(Spacer(1, 4))

    # Education
    story.append(Paragraph("Education", section_heading))
    story.append(Paragraph(data["education"], body_style))
    story.append(Spacer(1, 6))

    # Certifications
    if data["certifications"]:
        story.append(Paragraph("Certifications", section_heading))
        for cert in data["certifications"]:
            story.append(Paragraph(f"• {cert}", bullet_style))
        story.append(Spacer(1, 6))

    # Projects
    if data["projects"]:
        story.append(Paragraph("Key Projects", section_heading))
        for proj in data["projects"]:
            story.append(Paragraph(f"• {proj}", bullet_style))

    doc.build(story)


def create_docx_resume(data: dict, filepath: str):
    """Generates a professional DOCX resume using python-docx."""
    doc = docx.Document()

    # Header: Name, Contact info
    name_heading = doc.add_heading(data["name"], level=0)
    name_heading.paragraph_format.space_after = docx.shared.Pt(2)

    p_contact = doc.add_paragraph()
    p_contact.add_run(f"{data['email']}  |  {data['phone']}  |  {data.get('title', '')}").font.size = docx.shared.Pt(9.5)
    p_contact.paragraph_format.space_after = docx.shared.Pt(8)

    # Summary
    doc.add_heading("Professional Summary", level=2)
    doc.add_paragraph(data["summary"])

    # Skills
    doc.add_heading("Technical Skills", level=2)
    doc.add_paragraph(data["skills"])

    # Experience
    doc.add_heading("Work Experience", level=2)
    if data["experience"]:
        for exp in data["experience"]:
            p_role = doc.add_paragraph()
            r_bold = p_role.add_run(f"{exp['role']} - {exp['company']}")
            r_bold.bold = True
            p_role.add_run(f" ({exp['dates']})")
            for pt in exp["points"]:
                p_bullet = doc.add_paragraph(pt, style='List Bullet')
                p_bullet.paragraph_format.space_after = docx.shared.Pt(2)
    else:
        doc.add_paragraph("Fresher seeking entry-level software engineering opportunities.")

    # Education
    doc.add_heading("Education", level=2)
    doc.add_paragraph(data["education"])

    # Certifications
    if data["certifications"]:
        doc.add_heading("Certifications", level=2)
        for cert in data["certifications"]:
            doc.add_paragraph(cert, style='List Bullet')

    # Projects
    if data["projects"]:
        doc.add_heading("Key Projects", level=2)
        for proj in data["projects"]:
            doc.add_paragraph(proj, style='List Bullet')

    doc.save(filepath)


def generate_all_resumes():
    """Generates all 12 synthetic resumes in sample_data/resumes/."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generated = []

    for item in CANDIDATE_DATA:
        filepath = os.path.join(OUTPUT_DIR, item["filename"])
        if item["format"] == "pdf":
            create_pdf_resume(item, filepath)
        else:
            create_docx_resume(item, filepath)
        generated.append(filepath)
        print(f"Generated: {item['filename']} ({item['format'].upper()})")

    print(f"\nSuccessfully generated {len(generated)} synthetic resumes in: {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_all_resumes()
