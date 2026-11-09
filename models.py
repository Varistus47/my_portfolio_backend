"""SQLAlchemy ORM models (2.x declarative style, typed with Mapped[]).

Each model carries read-only properties for the values the API exposes but the
database does not store directly (`photo_url`, `image_url`, `contact`, ...).
That lets the Pydantic schemas in schemas.py use `from_attributes=True` and
validate an ORM instance straight through, with no hand-written mapping.

Table and column names match the original schema exactly, so the existing
portfolio.db keeps working - `create_all` is a no-op on tables that exist.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _public_url(filename: str | None) -> str | None:
    """Root-relative URL served by the /uploads static mount."""
    if not filename:
        return None
    return f"/uploads/{filename}"


def join_csv(values: list[str] | None) -> str:
    """['React', 'FastAPI'] -> 'React, FastAPI' for the tech_stack columns."""
    if not values:
        return ""
    return ", ".join(part.strip() for part in values if part and part.strip())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # SQLAlchemy sets this on every UPDATE
    )


class OrderedMixin:
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )


# --------------------------------------------------------------------- profile


class Profile(Base, TimestampMixin):
    """Singleton row. The CHECK keeps a second row impossible."""

    __tablename__ = "profile"
    __table_args__ = (CheckConstraint("id = 1", name="ck_profile_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    full_name: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    headline: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    tagline: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    about: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")

    photo_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_original_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    phone: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    email: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    address: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    linkedin_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    github_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    leetcode_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    website_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")

    # --- derived, read by the Pydantic schemas ---

    @property
    def photo_url(self) -> str | None:
        return _public_url(self.photo_filename)

    @property
    def has_resume(self) -> bool:
        return bool(self.resume_filename)

    @property
    def resume_url(self) -> str | None:
        return "/api/resume" if self.resume_filename else None

    @property
    def contact(self) -> dict[str, str]:
        """Stored flat, exposed nested: the frontend gets one object to iterate."""
        return {
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "leetcode_url": self.leetcode_url,
            "website_url": self.website_url,
        }

    @property
    def resume_download_name(self) -> str:
        name = (self.full_name or "").strip()
        if name:
            return f"{'_'.join(name.split())}_Resume.pdf"
        return (self.resume_original_name or "").strip() or "resume.pdf"


# ---------------------------------------------------------------------- skills


class Skill(Base, TimestampMixin, OrderedMixin):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 5", name="ck_skills_level"),
        Index("idx_skills_order", "display_order", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    # Free text on purpose, not an Enum: new categories must be addable from
    # admin without a schema migration.
    category: Mapped[str] = mapped_column(
        String(80), nullable=False, default="Other", server_default="Other"
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")


# -------------------------------------------------------------------- projects


class Project(Base, TimestampMixin, OrderedMixin):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("featured IN (0, 1)", name="ck_projects_featured"),
        Index("idx_projects_order", "display_order", "id"),
        Index("idx_projects_featured", "featured", "display_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    # Comma-separated; the schema splits it into a list. A join table would be
    # correct relational modelling and wrong engineering for a tag list the
    # admin types as "React, FastAPI, SQLite".
    tech_stack: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    github_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    live_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    image_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SQLite has no BOOLEAN; stored 0/1 and coerced to bool on the way out.
    featured: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    start_date: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    end_date: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")

    @property
    def image_url(self) -> str | None:
        return _public_url(self.image_filename)


# ------------------------------------------------------------------- education


class Education(Base, TimestampMixin, OrderedMixin):
    __tablename__ = "education"
    __table_args__ = (Index("idx_education_order", "display_order", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    field: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    location: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    start_date: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    end_date: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    grade: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")


# ------------------------------------------------------------------ experience


class Experience(Base, TimestampMixin, OrderedMixin):
    __tablename__ = "experience"
    __table_args__ = (
        CheckConstraint("is_current IN (0, 1)", name="ck_experience_is_current"),
        Index("idx_experience_order", "display_order", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    location: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    employment_type: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    start_date: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    end_date: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    is_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    tech_stack: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
