"""
Test app endpoints and validations.
"""

import sys
import os
import unittest
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


class AuScribeAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["app"], "AuScribe")
        self.assertIn("en", data["supported_languages"])
        self.assertIn("hi", data["supported_languages"])
        self.assertIn("bn", data["supported_languages"])

    def test_manifest(self):
        res = self.client.get("/manifest.json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["short_name"], "AuScribe")

    def test_service_worker(self):
        res = self.client.get("/sw.js")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"CACHE_NAME", res.data)

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"AuScribe", res.data)
        self.assertIn(b"English", res.data)
        self.assertIn(b"\xe0\xa4\xb9\xe0\xa4\xbf\xe0\xa4\xa8\xe0\xa5\x8d\xe0\xa4\xa6\xe0\xa5\x80", res.data)  # हिन्दी
        self.assertIn(b"\xe0\xa6\xac\xe0\xa6\xbe\xe0\xa6\x82\xe0\xa6\xb2\xe0\xa6\xbe", res.data)  # বাংলা

    def test_missing_api_key_subscription(self):
        # Without setting ELEVENLABS_API_KEY
        os.environ.pop("ELEVENLABS_API_KEY", None)
        res = self.client.get("/api/subscription")
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertIn("API key missing", data["error"])

    def test_invalid_language_transcribe(self):
        # Post invalid language code
        data = {
            "audio": (io.BytesIO(b"fake audio data"), "test.mp3"),
            "language_code": "fr",  # Not in en, hi, bn
        }
        res = self.client.post(
            "/api/transcribe",
            headers={"X-ElevenLabs-Key": "test_key"},
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("Invalid language code", data["error"])


if __name__ == "__main__":
    unittest.main()
