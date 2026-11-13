"""Tests for codebase scanner and digest generation."""

import unittest
from pathlib import Path
from repo_to_video.analyzer.scanner import CodebaseScanner
from repo_to_video.config import PROJECT_ROOT


class TestCodebaseScanner(unittest.TestCase):
    def test_scan_current_repo(self):
        scanner = CodebaseScanner(PROJECT_ROOT)
        digest = scanner.scan()

        self.assertIsNotNone(digest)
        self.assertGreater(digest.total_files, 0)
        self.assertIn("Python", digest.languages)
        self.assertTrue(len(digest.file_tree) > 0)
        
        summary_md = digest.to_markdown_summary()
        self.assertIn("# Codebase Digest:", summary_md)
        self.assertIn("Python", summary_md)


if __name__ == "__main__":
    unittest.main()
