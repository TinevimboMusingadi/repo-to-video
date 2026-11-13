"""Unit tests for FastAPI backend server."""

import unittest
from fastapi.testclient import TestClient
from repo_to_video.server import app
from repo_to_video.config import PROJECT_ROOT


class TestServerAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("gemini_configured", data)

    def test_list_videos(self):
        response = self.client.get("/api/videos")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("videos", data)
        self.assertIsInstance(data["videos"], list)

    def test_analyze_local_repo(self):
        response = self.client.post("/api/analyze", json={
            "repo_target": str(PROJECT_ROOT),
            "style": "motion"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("digest", data)
        self.assertIn("storyboard", data)
        self.assertGreater(len(data["storyboard"]["scenes"]), 0)


if __name__ == "__main__":
    unittest.main()
