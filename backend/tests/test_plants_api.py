import asyncio
import json
import unittest

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Plant
from app.routers.plants import router


async def asgi_request(app, method, path, payload=None):
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
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
            (b"content-type", b"application/json"),
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
    return response_start["status"], json.loads(response_body) if response_body else None


def request(app, method, path, payload=None):
    return asyncio.run(asgi_request(app, method, path, payload))


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

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db

    @classmethod
    def tearDownClass(cls):
        cls.app.dependency_overrides.clear()
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def plant_payload(self, **overrides):
        payload = {
            "name": "Monstera",
            "species": "Monstera deliciosa",
            "location": "Living Room",
            "date_acquired": "2024-03-12",
        }
        payload.update(overrides)
        return payload

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


if __name__ == "__main__":
    unittest.main()