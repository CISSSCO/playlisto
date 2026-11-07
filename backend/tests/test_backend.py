import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add backend to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import app.storage as storage
from app.drive import extract_folder_id
from app.streaming import guess_content_type
from fastapi.testclient import TestClient
from app.main import app


class TestDriveUtils(unittest.TestCase):
    def test_extract_folder_id(self):
        folder_id = "1z1wFXXyDYH-pIbjNbkOQkv5Zij8UDGIC"

        url1 = f"https://drive.google.com/drive/folders/{folder_id}"
        self.assertEqual(extract_folder_id(url1), folder_id)

        url2 = f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"
        self.assertEqual(extract_folder_id(url2), folder_id)

        url3 = f"https://drive.google.com/open?id={folder_id}"
        self.assertEqual(extract_folder_id(url3), folder_id)

        url4 = f"https://drive.google.com/drive/u/0/folders/{folder_id}/"
        self.assertEqual(extract_folder_id(url4), folder_id)

        # Raw ID
        self.assertEqual(extract_folder_id(folder_id), folder_id)

    def test_extract_folder_id_invalid(self):
        with self.assertRaises(ValueError):
            extract_folder_id("https://example.com/not-a-drive-url")

        with self.assertRaises(ValueError):
            extract_folder_id("short-id")

        with self.assertRaises(ValueError):
            extract_folder_id("")


class TestStreamingUtils(unittest.TestCase):
    def test_guess_content_type(self):
        self.assertEqual(guess_content_type("song.flac"), "audio/flac")
        self.assertEqual(guess_content_type("song.mp3"), "audio/mpeg")
        self.assertEqual(guess_content_type("song.wav"), "audio/wav")
        self.assertEqual(guess_content_type("song.m4a"), "audio/mp4")
        self.assertEqual(guess_content_type("song.ogg"), "audio/ogg")
        self.assertEqual(guess_content_type("unknown.xyz", "audio/flac"), "audio/flac")


class TestStorageAndAPI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_dir = Path(self.temp_dir.name)

        # Patch storage paths to use temp directory
        storage.DATA_DIR = self.test_data_dir
        storage.DATA_PATH = self.test_data_dir / "folders.json"
        storage.PROVIDERS_PATH = self.test_data_dir / "providers.enc"
        storage.SOURCES_PATH = self.test_data_dir / "sources.enc"
        storage.KEY_PATH = self.test_data_dir / "secret.key"

        self.client = TestClient(app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_provider_and_source_lifecycle(self):
        # 1. Add provider
        provider = storage.add_provider("Test Provider", "test-api-key-123")
        self.assertEqual(provider["name"], "Test Provider")
        self.assertIsNotNone(provider["id"])

        # Check metadata
        meta = storage.get_providers_metadata()
        self.assertEqual(len(meta), 1)
        self.assertEqual(meta[0]["name"], "Test Provider")
        self.assertTrue(meta[0]["active"])

        # Check get_provider_by_id
        found = storage.get_provider_by_id(provider["id"])
        self.assertIsNotNone(found)
        self.assertEqual(found["api_key"], "test-api-key-123")

        # 2. Add source
        source = storage.add_source(
            "Test Source",
            "https://drive.google.com/drive/folders/1z1wFXXyDYH-pIbjNbkOQkv5Zij8UDGIC",
            provider["id"]
        )
        self.assertEqual(source["name"], "Test Source")

        sources_data = storage.load_sources()
        self.assertEqual(len(sources_data["sources"]), 1)
        self.assertEqual(sources_data["active_source_id"], source["id"])

        # 3. Delete source
        storage.delete_source(source["id"])
        sources_after = storage.load_sources()
        self.assertEqual(len(sources_after["sources"]), 0)
        self.assertIsNone(sources_after["active_source_id"])

        # 4. Delete provider
        storage.delete_provider(provider["id"])
        meta_after = storage.get_providers_metadata()
        self.assertEqual(len(meta_after), 0)

    def test_api_endpoints(self):
        # When no active source exists
        no_source_res = self.client.post("/api/load-folder")
        self.assertEqual(no_source_res.status_code, 400)

        # Create Provider via API
        prov_res = self.client.post("/api/providers", json={"name": "API Provider", "api_key": "key123"})
        self.assertEqual(prov_res.status_code, 200)
        prov_id = prov_res.json()["id"]

        # List Providers
        list_res = self.client.get("/api/providers")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 1)

        # Create Source via API
        src_res = self.client.post("/api/sources", json={
            "name": "API Source",
            "url": "https://drive.google.com/drive/folders/1z1wFXXyDYH-pIbjNbkOQkv5Zij8UDGIC",
            "provider_id": prov_id
        })
        self.assertEqual(src_res.status_code, 200)

        # List Sources
        src_list = self.client.get("/api/sources")
        self.assertEqual(src_list.status_code, 200)
        self.assertEqual(len(src_list.json()["sources"]), 1)
        src_id = src_list.json()["sources"][0]["id"]

        # Delete Source via API
        del_src = self.client.delete(f"/api/sources/{src_id}")
        self.assertEqual(del_src.status_code, 200)

        # Delete Provider via API
        del_prov = self.client.delete(f"/api/providers/{prov_id}")
        self.assertEqual(del_prov.status_code, 200)

    def test_serve_frontend(self):
        # Frontend dist was built, so GET / should return index.html (200)
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))


if __name__ == "__main__":
    unittest.main()
