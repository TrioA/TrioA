import os
import subprocess
import sys
import tempfile
import unittest
from src.main import run_pipeline


class TestIntegration(unittest.TestCase):
    def test_run_pipeline_mock_and_dry_run(self):
        dark_svg, light_svg = run_pipeline(
            config_path="config/profile.yml",
            use_mock=True,
            dry_run=True,
            validate=True,
        )
        self.assertIn("<svg", dark_svg)
        self.assertIn("<svg", light_svg)

    def test_run_pipeline_output_to_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dark_svg, light_svg = run_pipeline(
                config_path="config/profile.yml",
                output_dir=tmpdir,
                dark_filename="d.svg",
                light_filename="l.svg",
                use_mock=True,
                dry_run=False,
                validate=True,
            )
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "d.svg")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "l.svg")))

    def test_cli_execution(self):
        cmd = [sys.executable, "src/main.py", "--mock", "--dry-run"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(
            "Profile generation completed successfully" in result.stderr
            or "Profile generation completed successfully" in result.stdout
        )


if __name__ == "__main__":
    unittest.main()
