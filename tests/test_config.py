import os
import tempfile
import unittest
from datetime import date

from src.config import ProfileConfig, PersonalConfig


class TestConfig(unittest.TestCase):
    def test_load_default_config(self):
        config = ProfileConfig.load_from_file("config/profile.yml")
        self.assertEqual(config.identity.username, "TrioA")
        self.assertEqual(config.identity.status_badge, "ONLINE")
        self.assertGreaterEqual(len(config.personal.operating_systems), 1)
        self.assertGreaterEqual(len(config.technical.languages), 1)
        self.assertGreaterEqual(len(config.projects), 1)
        self.assertIsInstance(config.custom_fields, dict)

    def test_calculate_uptime_iso_date(self):
        p = PersonalConfig(birthday="2000-01-01")
        ref = date(2025, 1, 1)
        uptime = p.calculate_uptime(reference_date=ref)
        self.assertIn("25 years", uptime)

    def test_calculate_uptime_custom_string(self):
        p = PersonalConfig(birthday="18 years, 5 months")
        uptime = p.calculate_uptime()
        self.assertEqual(uptime, "18 years, 5 months")

    def test_calculate_uptime_none(self):
        p = PersonalConfig(birthday=None)
        uptime = p.calculate_uptime()
        self.assertEqual(uptime, "N/A")

    def test_missing_optional_fields(self):
        minimal_data = {
            "identity": {"username": "TestDev"},
            "personal": {},
            "technical": {},
        }
        config = ProfileConfig.from_dict(minimal_data)
        self.assertEqual(config.identity.username, "TestDev")
        self.assertEqual(config.identity.status_badge, "ONLINE")
        self.assertEqual(config.personal.location, "Global")
        self.assertEqual(config.personal.operating_systems, ["Linux"])
        self.assertEqual(config.technical.languages, [])
        self.assertEqual(config.projects, [])
        self.assertEqual(config.hobbies, [])
        self.assertIsNone(config.links.website)
        self.assertIsNone(config.links.email)
        self.assertEqual(config.custom_fields, {})

    def test_nonexistent_config_file(self):
        with self.assertRaises(FileNotFoundError):
            ProfileConfig.load_from_file("nonexistent_path.yml")

    def test_invalid_yaml_root(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yml") as tf:
            tf.write("- item1\n- item2\n")
            temp_path = tf.name

        try:
            with self.assertRaises(ValueError):
                ProfileConfig.load_from_file(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
