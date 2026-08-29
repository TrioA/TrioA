import unittest
import xml.etree.ElementTree as ET
from src.config import ProfileConfig
from src.github_stats import GithubStats
from src.renderer import ProfileRenderer


class TestRenderer(unittest.TestCase):
    def test_renderer_generates_valid_xml(self):
        config = ProfileConfig.load_from_file("config/profile.yml")
        stats = GithubStats(
            repositories=15,
            stars=32,
            contributions=512,
            followers=20,
            commits=980,
            lines_added=45000,
            lines_deleted=12000,
            net_lines=33000,
            last_updated="2026-08-29 12:00 UTC",
        )

        renderer = ProfileRenderer(config, stats)
        
        # Dark Mode Validation
        dark_svg = renderer.render_svg("dark")
        dark_root = ET.fromstring(dark_svg)
        self.assertTrue(dark_root.tag.endswith("svg"))
        self.assertIn("width", dark_root.attrib)
        self.assertIn(config.identity.username.lower(), dark_svg)
        self.assertIn("980", dark_svg)  # commit count
        self.assertIn("45,000", dark_svg)  # lines added

        # Light Mode Validation
        light_svg = renderer.render_svg("light")
        light_root = ET.fromstring(light_svg)
        self.assertTrue(light_root.tag.endswith("svg"))
        self.assertIn(config.identity.username.lower(), light_svg)
        self.assertIn("980", light_svg)

    def test_renderer_with_empty_optional_fields(self):
        config = ProfileConfig.from_dict({
            "identity": {"username": "SoloDev"},
            "personal": {"location": "Mars"},
            "technical": {},
            "projects": [],
            "hobbies": [],
            "links": {},
            "custom_fields": {},
        })
        stats = GithubStats()
        renderer = ProfileRenderer(config, stats)

        dark_svg = renderer.render_svg("dark")
        root = ET.fromstring(dark_svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("solodev", dark_svg)


if __name__ == "__main__":
    unittest.main()
