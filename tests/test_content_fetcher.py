import unittest
from unittest.mock import MagicMock
from src.config import ProfileConfig
from src.content_fetcher import ContentFetcher


SAMPLE_DATA_JSON = {
    "personal": {
        "name": "Arav Gupta",
        "email": "hello@arav.is-a.dev",
        "location": "Gurugram, Haryana, India",
    },
    "skills": {
        "programming": ["C++", "JavaScript", "Python"],
        "web": ["React", "Vite"],
        "systems": ["Vulkan", "CMake"],
    },
    "projects": [
        {
            "title": "NODELAB",
            "summary": "A browser-based circuit simulator built from scratch with Canvas 2D.",
            "tags": ["JAVASCRIPT", "CANVAS 2D", "ELECTRONICS"],
            "importance": 1,
            "featured": True,
            "links": {"github": "https://github.com/TrioA/NodeLAB"},
        },
        {
            "title": "MODERNMINECRAFT",
            "summary": "A custom C++ Vulkan engine and multiplayer client.",
            "tags": ["C++", "VULKAN", "GLFW"],
            "importance": 2,
            "featured": True,
            "links": {"github": "https://github.com/TrioA"},
        },
        {
            "title": "NOT FEATURED",
            "summary": "Test",
            "importance": 99,
            "featured": False,
        },
    ],
    "services": [
        {"name": "CIRCUIT SIMULATION"},
        {"name": "3D & REAL-TIME GRAPHICS"},
    ],
}


class TestContentFetcher(unittest.TestCase):
    def test_content_fetcher_merging(self):
        base_config = ProfileConfig.load_from_file("config/profile.yml")
        fetcher = ContentFetcher()

        enhanced_config = fetcher.merge_with_config(base_config, raw_data=SAMPLE_DATA_JSON)

        self.assertEqual(enhanced_config.personal.location, "Gurugram, India")
        self.assertEqual(enhanced_config.links.email, "hello@arav.is-a.dev")
        self.assertEqual(enhanced_config.links.website, "https://arav.is-a.dev")
        self.assertEqual(len(enhanced_config.projects), 2)
        self.assertEqual(enhanced_config.projects[0].name, "NODELAB")
        self.assertEqual(enhanced_config.projects[1].name, "MODERNMINECRAFT")
        self.assertIn("C++", enhanced_config.technical.languages)
        self.assertIn("Vulkan", enhanced_config.technical.markup_and_configs)

    def test_content_fetcher_fallback_on_network_failure(self):
        base_config = ProfileConfig.load_from_file("config/profile.yml")
        fetcher = ContentFetcher()

        fallback_config = fetcher.merge_with_config(base_config, raw_data=None)

        self.assertEqual(fallback_config.identity.username, base_config.identity.username)
        self.assertEqual(len(fallback_config.projects), len(base_config.projects))


if __name__ == "__main__":
    unittest.main()
