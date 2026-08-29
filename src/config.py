"""
Configuration Loader and Validator
Loads profile configuration from YAML with type safety, fallbacks, and computed fields.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class IdentityConfig:
    username: str = "TrioA"
    status_badge: str = "ONLINE"


@dataclass
class PersonalConfig:
    birthday: Optional[str] = None
    location: str = "Global"
    operating_systems: List[str] = field(default_factory=lambda: ["Linux"])
    uptime_display: str = ""

    def calculate_uptime(self, reference_date: Optional[date] = None) -> str:
        """Calculates dynamic uptime/age based on birthday string or returns raw string."""
        if not self.birthday:
            return "N/A"

        ref = reference_date or date.today()
        # Try parsing ISO date YYYY-MM-DD
        try:
            birth_d = datetime.strptime(self.birthday.strip(), "%Y-%m-%d").date()
            if birth_d > ref:
                return "0 years, 0 months, 0 days"
            
            years = ref.year - birth_d.year
            months = ref.month - birth_d.month
            days = ref.day - birth_d.day

            if days < 0:
                months -= 1
                # Days in previous month
                prev_month = ref.month - 1 if ref.month > 1 else 12
                prev_year = ref.year if ref.month > 1 else ref.year - 1
                days += (date(ref.year, ref.month, 1) - date(prev_year, prev_month, 1)).days
            
            if months < 0:
                years -= 1
                months += 12

            year_str = f"{years} year" if years == 1 else f"{years} years"
            month_str = f"{months} month" if months == 1 else f"{months} months"
            day_str = f"{days} day" if days == 1 else f"{days} days"

            return f"{year_str}, {month_str}, {day_str}"
        except Exception:
            return str(self.birthday).strip()


@dataclass
class TechnicalConfig:
    languages: List[str] = field(default_factory=list)
    markup_and_configs: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)


@dataclass
class ProjectItem:
    name: str
    description: str
    tech: List[str] = field(default_factory=list)
    url: Optional[str] = None


@dataclass
class LinksConfig:
    website: Optional[str] = None
    email: Optional[str] = None


@dataclass
class ProfileConfig:
    identity: IdentityConfig = field(default_factory=IdentityConfig)
    personal: PersonalConfig = field(default_factory=PersonalConfig)
    technical: TechnicalConfig = field(default_factory=TechnicalConfig)
    projects: List[ProjectItem] = field(default_factory=list)
    hobbies: List[str] = field(default_factory=list)
    links: LinksConfig = field(default_factory=LinksConfig)
    custom_fields: Dict[str, str] = field(default_factory=dict)
    data_source: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProfileConfig:
        raw_identity = data.get("identity") or {}
        identity = IdentityConfig(
            username=str(raw_identity.get("username", "TrioA")),
            status_badge=str(raw_identity.get("status_badge", "ONLINE")),
        )

        raw_personal = data.get("personal") or {}
        personal = PersonalConfig(
            birthday=raw_personal.get("birthday"),
            location=str(raw_personal.get("location", "Global")),
            operating_systems=[str(x) for x in raw_personal.get("operating_systems", ["Linux"]) if x],
        )
        personal.uptime_display = personal.calculate_uptime()

        raw_tech = data.get("technical") or {}
        technical = TechnicalConfig(
            languages=[str(x) for x in raw_tech.get("languages", []) if x],
            markup_and_configs=[str(x) for x in raw_tech.get("markup_and_configs", []) if x],
            interests=[str(x) for x in raw_tech.get("interests", []) if x],
        )

        raw_projects = data.get("projects") or []
        projects: List[ProjectItem] = []
        for p in raw_projects:
            if isinstance(p, dict) and p.get("name"):
                projects.append(
                    ProjectItem(
                        name=str(p.get("name", "")),
                        description=str(p.get("description", "")),
                        tech=[str(t) for t in p.get("tech", []) if t],
                        url=str(p.get("url")) if p.get("url") else None,
                    )
                )

        raw_hobbies = data.get("hobbies") or []
        hobbies = [str(h) for h in raw_hobbies if h]

        raw_links = data.get("links") or {}
        links = LinksConfig(
            website=str(raw_links.get("website")) if raw_links.get("website") else None,
            email=str(raw_links.get("email")) if raw_links.get("email") else None,
        )

        raw_custom = data.get("custom_fields") or {}
        custom_fields = {str(k): str(v) for k, v in raw_custom.items() if k and v is not None}

        data_source = str(data.get("data_source")) if data.get("data_source") else None

        return cls(
            identity=identity,
            personal=personal,
            technical=technical,
            projects=projects,
            hobbies=hobbies,
            links=links,
            custom_fields=custom_fields,
            data_source=data_source,
        )

    @classmethod
    def load_from_file(cls, filepath: str) -> ProfileConfig:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found at: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f) or {}

        if not isinstance(content, dict):
            raise ValueError("YAML configuration root must be a mapping/dictionary")

        return cls.from_dict(content)
