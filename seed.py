"""Placeholder content inserted on first run only.

Every insert is guarded by a per-table row count, so `uvicorn --reload`
restarts never duplicate rows and never overwrite real content entered through
/admin.

No photo or resume is seeded: those need real files. The hero falls back to an
initials avatar and the resume button stays hidden until one is uploaded.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Base, Education, Experience, Profile, Project, Skill

_PROFILE = {
    "full_name": "Your Name",
    "headline": "Software Engineer",
    "tagline": "I build reliable backends and clean, fast interfaces.",
    "about": (
        "I'm a software engineer who enjoys turning messy problems into systems "
        "that are simple to reason about. Most of my work sits where a "
        "well-shaped API meets an interface that feels obvious to use.\n\n"
        "I care about the parts of engineering that show up months later: clear "
        "data models, tests that fail for the right reasons, and code the next "
        "person can change without fear. Outside of work I read about "
        "distributed systems and contribute to a few open-source projects.\n\n"
        "Replace this text from the admin page."
    ),
    "summary": (
        "Software engineer with hands-on experience building and shipping "
        "full-stack web applications. Comfortable across the stack: designing "
        "REST APIs and relational schemas on the backend, and building "
        "accessible, responsive interfaces on the frontend. Strong fundamentals "
        "in data structures, algorithms and system design, with a habit of "
        "writing maintainable, well-tested code."
    ),
    "phone": "+91 90000 00000",
    "email": "you@example.com",
    "address": "Chennai, Tamil Nadu, India",
    "linkedin_url": "https://www.linkedin.com/in/your-handle",
    "github_url": "https://github.com/your-handle",
    "leetcode_url": "https://leetcode.com/u/your-handle",
    "website_url": "https://your-domain.dev",
}

_SKILLS = [
    {"name": "Python", "category": "Languages", "level": 5, "display_order": 10},
    {"name": "TypeScript", "category": "Languages", "level": 4, "display_order": 20},
    {"name": "JavaScript", "category": "Languages", "level": 4, "display_order": 30},
    {"name": "SQL", "category": "Languages", "level": 4, "display_order": 40},
    {"name": "FastAPI", "category": "Frameworks", "level": 5, "display_order": 50},
    {"name": "SQLAlchemy", "category": "Frameworks", "level": 4, "display_order": 60},
    {"name": "React", "category": "Frameworks", "level": 4, "display_order": 70},
    {"name": "Tailwind CSS", "category": "Frameworks", "level": 4, "display_order": 80},
    {"name": "SQLite", "category": "Databases", "level": 4, "display_order": 90},
    {"name": "PostgreSQL", "category": "Databases", "level": 3, "display_order": 100},
    {"name": "Git & GitHub", "category": "Tools & DevOps", "level": 5, "display_order": 110},
    {"name": "Docker", "category": "Tools & DevOps", "level": 3, "display_order": 120},
    {"name": "Linux", "category": "Tools & DevOps", "level": 4, "display_order": 130},
]

_PROJECTS = [
    {
        "title": "Personal Portfolio Platform",
        "short_description": (
            "A database-driven portfolio with a hidden admin panel for live "
            "content editing."
        ),
        "description": (
            "A full-stack portfolio where every section is editable at runtime "
            "instead of hardcoded. A FastAPI backend exposes a REST API over "
            "SQLAlchemy and SQLite, with a password-gated admin console for "
            "full CRUD on projects, skills, education and experience, plus "
            "profile photo and resume PDF uploads. The React frontend renders "
            "everything from a single aggregate endpoint."
        ),
        "tech_stack": "React, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy, SQLite",
        "github_url": "https://github.com/your-handle/portfolio",
        "live_url": "",
        "featured": 1,
        "start_date": "Oct 2025",
        "end_date": "Present",
        "display_order": 10,
    },
    {
        "title": "Task Queue Service",
        "short_description": (
            "A lightweight job queue with retries, scheduling and a live dashboard."
        ),
        "description": (
            "A background job runner built to understand queueing from first "
            "principles. Supports delayed jobs, exponential-backoff retries, "
            "dead-letter handling and at-least-once delivery, with a small web "
            "dashboard for inspecting queue depth and failed jobs."
        ),
        "tech_stack": "Python, FastAPI, Redis, Docker",
        "github_url": "https://github.com/your-handle/task-queue",
        "live_url": "",
        "featured": 1,
        "start_date": "Apr 2025",
        "end_date": "Aug 2025",
        "display_order": 20,
    },
    {
        "title": "Expense Tracker API",
        "short_description": (
            "A REST API with JWT auth, category budgets and monthly reporting."
        ),
        "description": (
            "A personal finance backend covering authentication, recurring "
            "transactions, per-category budgets and aggregate monthly reports. "
            "Fully covered by pytest, including the date-boundary cases that "
            "make reporting code subtly wrong."
        ),
        "tech_stack": "Python, FastAPI, SQLAlchemy, PostgreSQL, pytest",
        "github_url": "https://github.com/your-handle/expense-tracker",
        "live_url": "",
        "featured": 0,
        "start_date": "Jan 2025",
        "end_date": "Mar 2025",
        "display_order": 30,
    },
]

_EDUCATION = [
    {
        "institution": "Your University",
        "degree": "B.E.",
        "field": "Computer Science and Engineering",
        "location": "Chennai, India",
        "start_date": "2021",
        "end_date": "2025",
        "grade": "8.5 / 10 CGPA",
        "description": (
            "Coursework in data structures, algorithms, operating systems, "
            "databases and computer networks.\n"
            "Final-year project on distributed task scheduling."
        ),
        "display_order": 10,
    },
]

_EXPERIENCE = [
    {
        "company": "Your Current Company",
        "role": "Software Engineer",
        "location": "Chennai, India",
        "employment_type": "Full-time",
        "start_date": "Jul 2025",
        "end_date": "",
        "is_current": 1,
        "description": (
            "Build and maintain REST APIs serving the core product, owning "
            "features end to end from schema design through release.\n"
            "Cut p95 latency on the busiest endpoint by roughly 40% by adding "
            "targeted indexes and removing an N+1 query.\n"
            "Raised backend test coverage and set up CI so regressions are "
            "caught before review rather than after deploy."
        ),
        "tech_stack": "Python, FastAPI, SQLAlchemy, PostgreSQL, Docker",
        "display_order": 10,
    },
    {
        "company": "Your Internship Company",
        "role": "Software Engineer Intern",
        "location": "Remote",
        "employment_type": "Internship",
        "start_date": "Jan 2025",
        "end_date": "Jun 2025",
        "is_current": 0,
        "description": (
            "Shipped an internal admin dashboard used daily by the operations "
            "team.\n"
            "Wrote the data-migration scripts for a schema change affecting "
            "several million rows, with a tested rollback path."
        ),
        "tech_stack": "React, TypeScript, Python",
        "display_order": 20,
    },
]


def _is_empty(session: Session, model: type[Base]) -> bool:
    count = session.scalar(select(func.count()).select_from(model))
    return not count


def _seed_profile(session: Session) -> None:
    """The profile row always exists; a blank name means 'never filled in'."""
    row = session.get(Profile, 1)
    if row is None or row.full_name:
        return
    for key, value in _PROFILE.items():
        setattr(row, key, value)


def seed_if_empty() -> None:
    with SessionLocal() as session:
        _seed_profile(session)

        for model, rows in (
            (Skill, _SKILLS),
            (Project, _PROJECTS),
            (Education, _EDUCATION),
            (Experience, _EXPERIENCE),
        ):
            if _is_empty(session, model):
                session.add_all([model(**values) for values in rows])

        session.commit()
