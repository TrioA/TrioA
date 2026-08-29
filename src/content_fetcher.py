"""
Dynamic Content Fetcher
Fetches live projects, skills, services, and profile data from remote sources (e.g., https://arav.is-a.dev/data.json)
with robust error handling, schema transformation, and local fallback.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import requests

from src.config import (
    IdentityConfig,
    LinksConfig,
    PersonalConfig,
    ProfileConfig,
    ProjectItem,
    TechnicalConfig,
)

logger = logging.getLogger("content_fetcher")


class ContentFetcher:
    DEFAULT_DATA_URL = "https://arav.is-a.dev/data.json"

    def __init__(self, data_url: Optional[str] = None, session: Optional[requests.Session] = None):
        self.data_url = data_url or self.DEFAULT_DATA_URL
        self.session = session or requests.Session()

    def fetch_raw_data(self) -> Optional[Dict[str, Any]]:
        """Fetches live JSON data with timeout and error isolation."""
        try:
            res = self.session.get(
                self.data_url,
                timeout=8,
                headers={"User-Agent": "Original-Profile-Generator/1.0", "Accept": "application/json"},
            )
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    return data
            logger.warning(f"Failed to fetch live content from {self.data_url}, status: {res.status_code}")
        except Exception as e:
            logger.warning(f"Exception fetching dynamic content from {self.data_url}: {e}")
        return None

    def merge_with_config(self, base_config: ProfileConfig, raw_data: Optional[Dict[str, Any]] = None) -> ProfileConfig:
        """
        Enhances base ProfileConfig with live data from data.json.
        Preserves base structure if dynamic fetch fails.
        """
        if raw_data is None:
            raw_data = self.fetch_raw_data()

        if not raw_data:
            logger.info("Using local profile configuration (remote data unavailable).")
            return base_config

        logger.info(f"Successfully integrated live content from {self.data_url}.")

        # 1. Identity & Links
        personal_data = raw_data.get("personal", {})
        email = personal_data.get("email") or base_config.links.email
        website = "https://arav.is-a.dev"
        location = personal_data.get("location") or base_config.personal.location

        # Clean location to broad format (e.g., "Gurugram, India")
        if location and "Haryana, India" in location:
            location = "Gurugram, India"

        links = LinksConfig(website=website, email=email)
        personal = PersonalConfig(
            birthday=base_config.personal.birthday,
            location=location,
            operating_systems=base_config.personal.operating_systems or ["Linux", "Windows"],
        )
        personal.uptime_display = personal.calculate_uptime()

        # 2. Technical Skills
        skills = raw_data.get("skills", {})
        programming_langs = skills.get("programming", []) or base_config.technical.languages
        
        # Merge web and systems for markup/infra
        web_skills = skills.get("web", [])
        systems_skills = skills.get("systems", [])
        hardware_skills = skills.get("hardware", [])
        
        infra_items = []
        for item in ["Vulkan", "React", "Vite", "Node.js", "CMake", "TCP Sockets", "Docker"]:
            if item in systems_skills or item in web_skills or item in programming_langs or item in ["Docker"]:
                if item not in programming_langs:
                    infra_items.append(item)
        if not infra_items:
            infra_items = base_config.technical.markup_and_configs

        # Services / Interests
        services = raw_data.get("services", [])
        interests = [s.get("name").title() for s in services if isinstance(s, dict) and s.get("name")]
        if not interests:
            interests = [
                "Circuit Simulation",
                "Vulkan & 3D Graphics",
                "Robotics & Embedded Systems",
                "Software Architecture",
            ]

        technical = TechnicalConfig(
            languages=programming_langs,
            markup_and_configs=infra_items[:6],
            interests=interests[:4],
        )

        # 3. Dynamic Featured Projects (Filtered by featured=True and sorted by importance)
        raw_projects = raw_data.get("projects", [])
        featured_projects = []
        for p in raw_projects:
            if isinstance(p, dict) and p.get("featured") is True:
                featured_projects.append(p)
        
        # Sort by importance (ascending: 1, 2, 3...)
        featured_projects.sort(key=lambda x: x.get("importance", 999))

        projects: List[ProjectItem] = []
        for p in featured_projects[:3]:
            name = p.get("title") or p.get("shortName") or "Project"
            # Summarize description concisely
            summary = p.get("summary", "")
            if "circuit simulator" in summary.lower():
                desc = "Browser-based interactive circuit simulator in Canvas 2D"
            elif "vulkan engine" in summary.lower():
                desc = "High-performance Vulkan game engine & multiplayer client"
            elif "e-commerce" in summary.lower():
                desc = "Production full-stack e-commerce platform with payments"
            elif "portfolio" in summary.lower():
                desc = "Technical portfolio with robotics & dynamic graphics"
            elif "robotics" in summary.lower():
                desc = "Autonomous robotics platform with computer vision"
            else:
                desc = summary[:48] if summary else "Featured software project"

            tags = p.get("tags", [])[:3]
            links_dict = p.get("links", {})
            url = links_dict.get("github") or links_dict.get("demo")

            projects.append(
                ProjectItem(
                    name=name,
                    description=desc,
                    tech=tags,
                    url=url,
                )
            )

        if not projects:
            projects = base_config.projects

        # 4. Custom Diagnostics Fields
        custom_fields = {
            "Current Focus": "Circuit Simulation & Vulkan Graphics",
            "Hardware Lab": "ESP32-CAM, Arduino, Robotics",
            "Discipline": "Hardware & Software Engineering",
            "Diagnostic": "ALL SYSTEMS NOMINAL",
        }

        # Hobbies
        hobbies = ["Robotics", "3D Modeling", "Electronics", "Sci-Fi"]

        return ProfileConfig(
            identity=base_config.identity,
            personal=personal,
            technical=technical,
            projects=projects,
            hobbies=hobbies,
            links=links,
            custom_fields=custom_fields,
        )
