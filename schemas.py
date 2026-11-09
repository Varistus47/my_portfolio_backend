"""Pydantic request/response models.

`*In` models are what admin forms send. `*Out` models set
`from_attributes=True`, so a SQLAlchemy ORM instance validates straight
through - `SkillOut.model_validate(skill)` reads the mapped columns and the
read-only properties declared on the models (`photo_url`, `image_url`,
`contact`, ...) with no hand-written mapping.

Two shape differences are handled by validators rather than by the caller:

* `tech_stack` is a comma-separated TEXT column but a `list[str]` in the API,
  so a `mode="before"` validator splits it.
* `featured` / `is_current` are INTEGER 0/1 in SQLite (it has no BOOLEAN) and
  `bool` in the API; Pydantic coerces those automatically.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Shared config for every response model that reads an ORM instance.
ORM = ConfigDict(from_attributes=True)
# Request models trim incoming whitespace.
FORM = ConfigDict(str_strip_whitespace=True)


def _as_list(value: object) -> object:
    """Accept either the stored CSV string or an already-parsed list."""
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return value


# ----------------------------------------------------------------------- admin


class LoginIn(BaseModel):
    password: str


class TokenOut(BaseModel):
    token: str
    expires_in: int


class SessionOut(BaseModel):
    valid: bool


# --------------------------------------------------------------------- profile


class ContactOut(BaseModel):
    model_config = ORM

    phone: str
    email: str
    address: str
    linkedin_url: str
    github_url: str
    leetcode_url: str
    website_url: str


class ProfileIn(BaseModel):
    """Flat, mirroring the single admin form. Filenames are not settable here -
    they change only through the upload and delete endpoints."""

    model_config = FORM

    full_name: str = ""
    headline: str = ""
    tagline: str = ""
    about: str = ""
    summary: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    leetcode_url: str = ""
    website_url: str = ""


class ProfileOut(BaseModel):
    model_config = ORM

    full_name: str
    headline: str
    tagline: str
    about: str
    summary: str
    photo_url: str | None
    has_resume: bool
    resume_url: str | None
    contact: ContactOut
    updated_at: datetime


class PhotoOut(BaseModel):
    photo_url: str


class ResumeOut(BaseModel):
    resume_url: str
    resume_original_name: str


class ImageOut(BaseModel):
    image_url: str


# ---------------------------------------------------------------------- skills


class SkillIn(BaseModel):
    model_config = FORM

    name: str = Field(min_length=1, max_length=80)
    category: str = Field(default="Other", max_length=80)
    level: int = Field(default=3, ge=1, le=5)
    display_order: int | None = None


class SkillOut(BaseModel):
    model_config = ORM

    id: int
    name: str
    category: str
    level: int
    display_order: int


# -------------------------------------------------------------------- projects


class ProjectIn(BaseModel):
    model_config = FORM

    title: str = Field(min_length=1, max_length=200)
    short_description: str = ""
    description: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    github_url: str = ""
    live_url: str = ""
    featured: bool = False
    start_date: str = ""
    end_date: str = ""
    display_order: int | None = None


class ProjectOut(BaseModel):
    model_config = ORM

    id: int
    title: str
    short_description: str
    description: str
    tech_stack: list[str]
    github_url: str
    live_url: str
    image_url: str | None
    featured: bool
    start_date: str
    end_date: str
    display_order: int

    _split_tech = field_validator("tech_stack", mode="before")(_as_list)


# ------------------------------------------------------------------- education


class EducationIn(BaseModel):
    model_config = FORM

    institution: str = Field(min_length=1, max_length=200)
    degree: str = ""
    field: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    grade: str = ""
    description: str = ""
    display_order: int | None = None


class EducationOut(BaseModel):
    model_config = ORM

    id: int
    institution: str
    degree: str
    field: str
    location: str
    start_date: str
    end_date: str
    grade: str
    description: str
    display_order: int


# ------------------------------------------------------------------ experience


class ExperienceIn(BaseModel):
    model_config = FORM

    company: str = Field(min_length=1, max_length=200)
    role: str = ""
    location: str = ""
    employment_type: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    description: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    display_order: int | None = None


class ExperienceOut(BaseModel):
    model_config = ORM

    id: int
    company: str
    role: str
    location: str
    employment_type: str
    start_date: str
    end_date: str
    is_current: bool
    description: str
    tech_stack: list[str]
    display_order: int

    _split_tech = field_validator("tech_stack", mode="before")(_as_list)


# -------------------------------------------------------------- aggregate view


class PortfolioOut(BaseModel):
    """Everything the home page needs, in one response."""

    model_config = ORM

    profile: ProfileOut
    skills: list[SkillOut]
    projects: list[ProjectOut]
    education: list[EducationOut]
    experience: list[ExperienceOut]
