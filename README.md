# Plant Inventory

## Continuous integration

GitHub Actions runs independent frontend and backend checks on every push and pull request. The workflow uses read-only repository permissions.

- **Frontend** (Node.js 22): `npm ci`, `npm run lint`, and `npm run build` from `frontend/`.
- **Backend** (Python 3.11): install `backend/requirements.txt`, then run `python -m unittest discover -s tests -v` from `backend/`.

Backend endpoint tests use an isolated in-memory SQLite database and do not require or modify the development PostgreSQL database. The current backend tests use Python's standard-library `unittest`, so no additional test dependencies are needed.

## Test on a phone

Connect the phone and development computer to the same Wi-Fi network. Find the computer's LAN IPv4 address (on macOS, `ipconfig getifaddr en0`). From the `backend/` directory, start the API bound to the network interface and allow the frontend's exact origin:

```sh
PLANT_INVENTORY_CORS_ORIGINS=http://<computer-ip>:5173 .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

From `frontend/`, start Vite with its API URL pointed at that same computer address:

```sh
VITE_API_URL=http://<computer-ip>:8000 npm run dev -- --host 0.0.0.0 --port 5173
```

Replace `<computer-ip>` with the LAN address in both commands, then open `http://<computer-ip>:5173` on the phone. The frontend otherwise uses `http://127.0.0.1:8000`, which would refer to the phone itself. CORS is restricted to `http://localhost:5173` by default; the environment variable adds the exact LAN frontend origin for this session. If the phone cannot connect, check the computer firewall and ensure the Wi-Fi network permits device-to-device connections.
