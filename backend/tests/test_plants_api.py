import asyncio
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
import av
from PIL import Image
from pillow_heif import from_pillow
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Plant, PlantPhoto
from app.routers.plants import router
from app.storage import LocalPhotoStorage, get_photo_storage


async def asgi_request(app, method, path, payload=None, raw_body=None, content_type="application/json"):
    body = raw_body if raw_body is not None else b"" if payload is None else json.dumps(payload).encode("utf-8")
    messages = []
    request_sent = False

    async def receive():
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    raw_path = path.encode("utf-8")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": raw_path,
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", content_type.encode("ascii")),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    await app(scope, receive, send)
    response_start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    headers = dict(response_start["headers"])
    response_content_type = headers.get(b"content-type", b"").decode("latin-1")
    data = json.loads(response_body) if "application/json" in response_content_type else response_body
    return response_start["status"], data


def request(app, method, path, payload=None, raw_body=None, content_type="application/json"):
    return asyncio.run(asgi_request(app, method, path, payload, raw_body, content_type))


class PlantEndpointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.SessionLocal = sessionmaker(bind=cls.engine, autoflush=False, autocommit=False)
        cls.app = FastAPI()
        cls.app.include_router(router)
        cls.upload_directory = tempfile.TemporaryDirectory()
        cls.storage = LocalPhotoStorage(cls.upload_directory.name)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.app.dependency_overrides[get_photo_storage] = lambda: cls.storage

    @classmethod
    def tearDownClass(cls):
        cls.app.dependency_overrides.clear()
        cls.engine.dispose()
        cls.upload_directory.cleanup()

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        for item in Path(self.upload_directory.name).iterdir():
            item.unlink()

    def plant_payload(self, **overrides):
        payload = {
            "name": "Monstera",
            "species": "Monstera deliciosa",
            "location": "Living Room",
            "date_acquired": "2024-03-12",
        }
        payload.update(overrides)
        return payload

    def create_plant(self):
        status, plant = request(self.app, "POST", "/plants/", self.plant_payload())
        self.assertEqual(status, 200)
        return plant

    @staticmethod
    def image_bytes(image_format="PNG", color=(30, 150, 90)):
        image = Image.new("RGB", (8, 8), color)
        output = BytesIO()
        image.save(output, format=image_format)
        return output.getvalue()

    @staticmethod
    def mpo_bytes():
        first = Image.new("RGB", (8, 8), (30, 150, 90))
        second = Image.new("RGB", (8, 8), (90, 30, 150))
        output = BytesIO()
        first.save(output, format="MPO", save_all=True, append_images=[second])
        return output.getvalue()

    @staticmethod
    def heic_bytes():
        source = (
            "from io import BytesIO; from PIL import Image; "
            "from pillow_heif import from_pillow; import sys; "
            "output = BytesIO(); "
            "from_pillow(Image.new('RGB', (8, 8), (30, 150, 90))).save(output, format='HEIF'); "
            "sys.stdout.buffer.write(output.getvalue())"
        )
        return subprocess.check_output([sys.executable, "-c", source])

    @staticmethod
    def avif_bytes():
        output = BytesIO()
        from_pillow(Image.new("RGB", (8, 8), (90, 150, 30))).save(output, format="AVIF")
        return output.getvalue()

    @staticmethod
    def mov_bytes(duration_seconds=1):
        output_buffer = BytesIO()
        with av.open(output_buffer, mode="w", format="mov") as output:
            stream = output.add_stream("mpeg4", rate=1)
            stream.width = 16
            stream.height = 16
            stream.pix_fmt = "yuv420p"
            for _ in range(duration_seconds):
                frame = av.VideoFrame.from_image(Image.new("RGB", (16, 16), (120, 40, 80)))
                for packet in stream.encode(frame):
                    output.mux(packet)
            for packet in stream.encode():
                output.mux(packet)
        return output_buffer.getvalue()

    def upload_photo(self, plant_id, content=None, filename="garden.png", content_type="image/png", fields=None):
        boundary = "photo-test-boundary"
        parts = []
        for name, value in (fields or {}).items():
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
            )
        parts.append(
            (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode()
            + (content if content is not None else self.image_bytes())
            + b"\r\n"
        )
        body = b"".join(parts) + f"--{boundary}--\r\n".encode()
        return request(
            self.app,
            "POST",
            f"/plants/{plant_id}/photos",
            raw_body=body,
            content_type=f"multipart/form-data; boundary={boundary}",
        )

    def test_create_list_fetch_update_and_persist_across_sessions(self):
        status, created = request(self.app, "POST", "/plants/", self.plant_payload())
        self.assertEqual(status, 200)
        self.assertEqual(created["name"], "Monstera")
        self.assertEqual(created["date_acquired"], "2024-03-12")
        plant_id = created["id"]

        status, plants = request(self.app, "GET", "/plants/")
        self.assertEqual(status, 200)
        self.assertEqual([plant["id"] for plant in plants], [plant_id])

        status, fetched = request(self.app, "GET", f"/plants/{plant_id}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched, created)

        updated_payload = self.plant_payload(
            name="Updated Monstera",
            location="Office",
            date_acquired="2024-04-01",
        )
        status, updated = request(self.app, "PUT", f"/plants/{plant_id}", updated_payload)
        self.assertEqual(status, 200)
        self.assertEqual(updated["name"], "Updated Monstera")
        self.assertEqual(updated["location"], "Office")
        self.assertEqual(updated["date_acquired"], "2024-04-01")

        with self.SessionLocal() as db:
            saved_plant = db.get(Plant, plant_id)
            self.assertIsNotNone(saved_plant)
            self.assertEqual(saved_plant.name, "Updated Monstera")
            self.assertEqual(saved_plant.location, "Office")

    def test_delete_removes_plant(self):
        _, created = request(self.app, "POST", "/plants/", self.plant_payload())

        status, result = request(self.app, "DELETE", f"/plants/{created['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(result, {"message": "Plant deleted successfully"})
        self.assertEqual(request(self.app, "GET", f"/plants/{created['id']}")[0], 404)

    def test_missing_ids_return_404_for_fetch_update_and_delete(self):
        missing_id = 9999
        self.assertEqual(request(self.app, "GET", f"/plants/{missing_id}")[0], 404)
        self.assertEqual(
            request(self.app, "PUT", f"/plants/{missing_id}", self.plant_payload())[0],
            404,
        )
        self.assertEqual(request(self.app, "DELETE", f"/plants/{missing_id}")[0], 404)

    def test_invalid_request_data_returns_422_without_saving(self):
        missing_field_payload = self.plant_payload()
        del missing_field_payload["name"]
        status, _ = request(self.app, "POST", "/plants/", missing_field_payload)
        self.assertEqual(status, 422)

        invalid_date_payload = self.plant_payload(date_acquired="not-a-date")
        status, _ = request(self.app, "POST", "/plants/", invalid_date_payload)
        self.assertEqual(status, 422)

        status, plants = request(self.app, "GET", "/plants/")
        self.assertEqual(status, 200)
        self.assertEqual(plants, [])

    def test_photo_upload_timeline_thumbnail_and_media_response(self):
        plant = self.create_plant()
        older_bytes = self.image_bytes("PNG", (20, 80, 180))
        newer_bytes = self.image_bytes("JPEG", (180, 80, 20))

        status, older = self.upload_photo(
            plant["id"],
            older_bytes,
            fields={"date_taken": "2024-01-15", "caption": "Winter leaves"},
        )
        self.assertEqual(status, 201)
        self.assertEqual(older["caption"], "Winter leaves")
        status, newer = self.upload_photo(
            plant["id"],
            newer_bytes,
            filename="untrusted.jpeg",
            content_type="application/octet-stream",
            fields={"date_taken": "2024-02-20", "caption": "New growth"},
        )
        self.assertEqual(status, 201)

        status, timeline = request(self.app, "GET", f"/plants/{plant['id']}/photos")
        self.assertEqual(status, 200)
        self.assertEqual([photo["id"] for photo in timeline], [newer["id"], older["id"]])
        self.assertEqual(timeline[0]["date_taken"], "2024-02-20")

        status, plants = request(self.app, "GET", "/plants/")
        self.assertEqual(status, 200)
        self.assertEqual(plants[0]["latest_photo_url"], newer["image_url"])

        status, image = request(self.app, "GET", newer["image_url"])
        self.assertEqual(status, 200)
        self.assertEqual(image, newer_bytes)

        with self.SessionLocal() as db:
            persisted_photo = db.get(PlantPhoto, newer["id"])
            self.assertIsNotNone(persisted_photo)
            self.assertEqual(persisted_photo.date_taken, date(2024, 2, 20))
            self.assertEqual(persisted_photo.content_type, "image/jpeg")
            self.assertTrue(self.storage.path_for(persisted_photo.storage_key).is_file())

    def test_photo_delete_removes_only_photo_and_file(self):
        plant = self.create_plant()
        status, photo = self.upload_photo(plant["id"])
        self.assertEqual(status, 201)
        with self.SessionLocal() as db:
            storage_key = db.get(PlantPhoto, photo["id"]).storage_key

        status, result = request(
            self.app,
            "DELETE",
            f"/plants/{plant['id']}/photos/{photo['id']}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(result, {"message": "Photo deleted successfully"})
        self.assertFalse(self.storage.path_for(storage_key).exists())
        self.assertEqual(request(self.app, "GET", f"/plants/{plant['id']}/photos")[1], [])
        self.assertEqual(request(self.app, "GET", f"/plants/{plant['id']}")[0], 200)

    def test_webp_upload_defaults_date_and_allows_empty_caption(self):
        plant = self.create_plant()
        status, photo = self.upload_photo(
            plant["id"],
            self.image_bytes("WEBP"),
            filename="plant.webp",
            content_type="image/webp",
        )
        self.assertEqual(status, 201)
        self.assertEqual(photo["date_taken"], date.today().isoformat())
        self.assertIsNone(photo["caption"])
        with self.SessionLocal() as db:
            saved_photo = db.get(PlantPhoto, photo["id"])
            self.assertEqual(saved_photo.content_type, "image/webp")

    def test_mpo_stereo_photo_is_converted_to_primary_jpeg_frame(self):
        plant = self.create_plant()
        status, photo = self.upload_photo(
            plant["id"],
            self.mpo_bytes(),
            filename="iphone-stereo.mpo",
            content_type="image/mpo",
        )
        self.assertEqual(status, 201)
        with self.SessionLocal() as db:
            saved_photo = db.get(PlantPhoto, photo["id"])
            self.assertEqual(saved_photo.content_type, "image/jpeg")
            self.assertTrue(saved_photo.storage_key.endswith(".jpg"))

        status, stored_image = request(self.app, "GET", photo["image_url"])
        self.assertEqual(status, 200)
        with Image.open(BytesIO(stored_image)) as decoded:
            self.assertEqual(decoded.format, "JPEG")

    def test_iphone_heic_upload_is_converted_to_browser_compatible_jpeg(self):
        plant = self.create_plant()
        status, photo = self.upload_photo(
            plant["id"],
            self.heic_bytes(),
            filename="iphone-photo.heic",
            content_type="image/heic",
        )
        self.assertEqual(status, 201)
        with self.SessionLocal() as db:
            saved_photo = db.get(PlantPhoto, photo["id"])
            self.assertEqual(saved_photo.content_type, "image/jpeg")
            self.assertTrue(saved_photo.storage_key.endswith(".jpg"))

        status, stored_image = request(self.app, "GET", photo["image_url"])
        self.assertEqual(status, 200)
        with Image.open(BytesIO(stored_image)) as decoded:
            self.assertEqual(decoded.format, "JPEG")

    def test_avif_upload_is_converted_to_browser_compatible_jpeg(self):
        plant = self.create_plant()
        status, photo = self.upload_photo(
            plant["id"],
            self.avif_bytes(),
            filename="iphone-photo.avif",
            content_type="image/avif",
        )
        self.assertEqual(status, 201)
        with self.SessionLocal() as db:
            saved_photo = db.get(PlantPhoto, photo["id"])
            self.assertEqual(saved_photo.content_type, "image/jpeg")
            self.assertTrue(saved_photo.storage_key.endswith(".jpg"))

        status, stored_image = request(self.app, "GET", photo["image_url"])
        self.assertEqual(status, 200)
        with Image.open(BytesIO(stored_image)) as decoded:
            self.assertEqual(decoded.format, "JPEG")

    def test_live_photo_mov_upload_extracts_and_stores_only_a_jpeg_still(self):
        plant = self.create_plant()
        status, photo = self.upload_photo(
            plant["id"],
            self.mov_bytes(),
            filename="IMG_1234.MOV",
            content_type="video/quicktime",
        )
        self.assertEqual(status, 201)
        with self.SessionLocal() as db:
            saved_photo = db.get(PlantPhoto, photo["id"])
            self.assertEqual(saved_photo.content_type, "image/jpeg")
            self.assertTrue(saved_photo.storage_key.endswith(".jpg"))

        status, still_image = request(self.app, "GET", photo["image_url"])
        self.assertEqual(status, 200)
        with Image.open(BytesIO(still_image)) as decoded:
            self.assertEqual(decoded.format, "JPEG")

    def test_live_photo_detects_mov_without_filename_or_video_mime(self):
        plant = self.create_plant()
        status, photo = self.upload_photo(
            plant["id"],
            self.mov_bytes(),
            filename="upload",
            content_type="application/octet-stream",
        )
        self.assertEqual(status, 201)
        with self.SessionLocal() as db:
            saved_photo = db.get(PlantPhoto, photo["id"])
            self.assertEqual(saved_photo.content_type, "image/jpeg")

    def test_live_photo_video_can_exceed_still_image_limit(self):
        plant = self.create_plant()
        mov_data = self.mov_bytes() + b"\x00" * (10 * 1024 * 1024 + 1)
        status, photo = self.upload_photo(
            plant["id"],
            mov_data,
            filename="IMG_1234.MOV",
            content_type="video/quicktime",
        )
        self.assertEqual(status, 201)
        with self.SessionLocal() as db:
            saved_photo = db.get(PlantPhoto, photo["id"])
            self.assertEqual(saved_photo.content_type, "image/jpeg")

    def test_live_photo_video_duration_limit_is_enforced(self):
        plant = self.create_plant()
        status, error = self.upload_photo(
            plant["id"],
            self.mov_bytes(duration_seconds=31),
            filename="long-motion.MOV",
            content_type="video/quicktime",
        )
        self.assertEqual(status, 413)
        self.assertIn("30 seconds", error["detail"])

    def test_deleting_plant_removes_all_photo_records_and_files(self):
        plant = self.create_plant()
        self.upload_photo(plant["id"])
        self.upload_photo(plant["id"], fields={"date_taken": "2024-04-01"})
        with self.SessionLocal() as db:
            storage_keys = [photo.storage_key for photo in db.query(PlantPhoto).all()]

        status, _ = request(self.app, "DELETE", f"/plants/{plant['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(request(self.app, "GET", f"/plants/{plant['id']}")[0], 404)
        with self.SessionLocal() as db:
            self.assertEqual(db.query(PlantPhoto).count(), 0)
        self.assertTrue(all(not self.storage.path_for(key).exists() for key in storage_keys))

    def test_upload_rejects_invalid_unsupported_and_oversized_images(self):
        plant = self.create_plant()
        status, invalid = self.upload_photo(plant["id"], b"this is not an image")
        self.assertEqual(status, 400)
        self.assertIn("not a valid image", invalid["detail"])

        gif_bytes = self.image_bytes("GIF")
        status, unsupported = self.upload_photo(plant["id"], gif_bytes, filename="plant.gif")
        self.assertEqual(status, 415)
        self.assertIn("GIF", unsupported["detail"])
        self.assertIn("HEIC/HEIF", unsupported["detail"])

        oversized = b"x" * (10 * 1024 * 1024 + 1)
        status, too_large = self.upload_photo(plant["id"], oversized)
        self.assertEqual(status, 413)
        self.assertIn("10 MB", too_large["detail"])

        self.assertEqual(request(self.app, "GET", f"/plants/{plant['id']}/photos")[1], [])
        self.assertEqual(list(Path(self.upload_directory.name).iterdir()), [])

    def test_photo_routes_validate_plant_photo_and_form_fields(self):
        self.assertEqual(request(self.app, "GET", "/plants/999/photos")[0], 404)
        self.assertEqual(self.upload_photo(999)[0], 404)

        plant = self.create_plant()
        status, invalid_date = self.upload_photo(
            plant["id"], fields={"date_taken": "not-a-date"}
        )
        self.assertEqual(status, 422)
        self.assertEqual(
            request(self.app, "DELETE", f"/plants/{plant['id']}/photos/999")[0],
            404,
        )
        self.assertEqual(request(self.app, "GET", "/plants/photos/999/image")[0], 404)


class PhotoMigrationTest(unittest.TestCase):
    def test_upgrade_creates_schema_for_fresh_database(self):
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import inspect

        with tempfile.TemporaryDirectory() as directory:
            database_url = f"sqlite:///{Path(directory) / 'fresh.sqlite'}"
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            with patch.dict(os.environ, {"DATABASE_URL": database_url}):
                command.upgrade(config, "head")

            migrated_engine = create_engine(database_url)
            tables = set(inspect(migrated_engine).get_table_names())
            self.assertTrue({"plants", "plant_photos", "alembic_version"}.issubset(tables))
            migrated_engine.dispose()

    def test_upgrade_preserves_existing_plants_and_adds_photo_table(self):
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import inspect, text

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "existing.sqlite"
            database_url = f"sqlite:///{database_path}"
            existing_engine = create_engine(database_url)
            with existing_engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE plants (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, "
                    "species VARCHAR(150) NOT NULL, location VARCHAR(100) NOT NULL, date_acquired DATE NOT NULL)"
                ))
                connection.execute(text(
                    "INSERT INTO plants (id, name, species, location, date_acquired) "
                    "VALUES (1, 'Existing fern', 'Nephrolepis', 'Porch', '2020-05-02')"
                ))
            existing_engine.dispose()

            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            with patch.dict(os.environ, {"DATABASE_URL": database_url}):
                command.upgrade(config, "head")

            migrated_engine = create_engine(database_url)
            with migrated_engine.connect() as connection:
                row = connection.execute(text("SELECT id, name FROM plants WHERE id = 1")).one()
                self.assertEqual(tuple(row), (1, "Existing fern"))
            self.assertIn("plant_photos", inspect(migrated_engine).get_table_names())
            self.assertIn("alembic_version", inspect(migrated_engine).get_table_names())
            migrated_engine.dispose()


if __name__ == "__main__":
    unittest.main()