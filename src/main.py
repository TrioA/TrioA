"""
Main CLI Driver for GitHub Profile SVG Generator
Executes the full pipeline: config loading -> statistics collection -> SVG rendering -> XML validation -> asset writing.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cache_manager import CacheManager
from src.config import ProfileConfig
from src.content_fetcher import ContentFetcher
from src.github_stats import GithubStats, GithubStatsCollector
from src.renderer import ProfileRenderer

logger = logging.getLogger("profile_generator")


def validate_svg_content(svg_str: str) -> bool:
    """Validates that the generated SVG is well-formed XML."""
    try:
        root = ET.fromstring(svg_str)
        if not root.tag.endswith("svg"):
            return False
        return True
    except ET.ParseError as e:
        logger.error(f"SVG XML Validation Error: {e}")
        return False


def run_pipeline(
    config_path: str = "config/profile.yml",
    output_dir: str = "assets",
    dark_filename: str = "dark_mode.svg",
    light_filename: str = "light_mode.svg",
    use_mock: bool = False,
    force_refresh: bool = False,
    validate: bool = True,
    dry_run: bool = False,
    fetch_remote_content: bool = True,
) -> Tuple[str, str]:
    """Runs the profile generation pipeline and returns (dark_svg, light_svg)."""
    logger.info(f"Loading configuration from {config_path}...")
    config = ProfileConfig.load_from_file(config_path)

    # Dynamic Remote Content Fetching (e.g. from data.json)
    if fetch_remote_content and config.data_source and not use_mock:
        logger.info(f"Fetching dynamic content from {config.data_source}...")
        fetcher = ContentFetcher(data_url=config.data_source)
        config = fetcher.merge_with_config(config)

    # Statistics Collection
    if use_mock or os.getenv("GH_STATS_MOCK") == "1":
        logger.info(f"Using mock telemetry for user '{config.identity.username}'...")
        stats = GithubStatsCollector.get_mock_stats(config.identity.username)
    else:
        logger.info(f"Collecting dynamic GitHub statistics for '{config.identity.username}'...")
        cache = CacheManager()
        collector = GithubStatsCollector(username=config.identity.username, cache_manager=cache)
        stats = collector.collect(force_refresh=force_refresh)

    logger.info(
        f"Telemetry stats: Repos={stats.repositories}, Stars={stats.stars}, "
        f"Contributions={stats.contributions}, Commits={stats.commits}, "
        f"Additions=+{stats.lines_added}, Deletions=-{stats.lines_deleted}, Net LOC={stats.net_lines}"
    )

    # Rendering
    renderer = ProfileRenderer(config=config, stats=stats)
    dark_svg = renderer.render_svg(theme_name="dark")
    light_svg = renderer.render_svg(theme_name="light")

    # XML Validation
    if validate:
        if not validate_svg_content(dark_svg):
            raise ValueError("Dark mode SVG failed XML validation")
        if not validate_svg_content(light_svg):
            raise ValueError("Light mode SVG failed XML validation")
        logger.info("XML validation passed for both SVG themes.")

    # Write files
    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)
        dark_path = os.path.join(output_dir, dark_filename)
        light_path = os.path.join(output_dir, light_filename)

        with open(dark_path, "w", encoding="utf-8") as f:
            f.write(dark_svg)
        logger.info(f"Generated dark mode SVG: {dark_path}")

        with open(light_path, "w", encoding="utf-8") as f:
            f.write(light_svg)
        logger.info(f"Generated light mode SVG: {light_path}")

    return dark_svg, light_svg


def main() -> int:
    parser = argparse.ArgumentParser(description="Terminal GitHub Profile SVG Generator V1")
    parser.add_argument("--config", default="config/profile.yml", help="Path to profile.yml")
    parser.add_argument("--output-dir", default="assets", help="Directory for output SVGs")
    parser.add_argument("--dark-output", default="dark_mode.svg", help="Dark SVG filename")
    parser.add_argument("--light-output", default="light_mode.svg", help="Light SVG filename")
    parser.add_argument("--mock", action="store_true", help="Use mock telemetry for offline/testing")
    parser.add_argument("--force", action="store_true", help="Force refresh cache")
    parser.add_argument("--no-validate", action="store_true", help="Disable XML validation")
    parser.add_argument("--dry-run", action="store_true", help="Validate and render in memory only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error messages")

    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.ERROR

    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")

    try:
        run_pipeline(
            config_path=args.config,
            output_dir=args.output_dir,
            dark_filename=args.dark_output,
            light_filename=args.light_output,
            use_mock=args.mock,
            force_refresh=args.force,
            validate=not args.no_validate,
            dry_run=args.dry_run,
        )
        logger.info("Profile generation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
