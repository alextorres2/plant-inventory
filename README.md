# Plant Inventory

## Continuous integration

GitHub Actions runs independent frontend and backend checks on every push and pull request. The workflow uses read-only repository permissions.

- **Frontend** (Node.js 22): `npm ci`, `npm run lint`, and `npm run build` from `frontend/`.
- **Backend** (Python 3.11): install `backend/requirements.txt`, then run `python -m unittest discover -s tests -v` from `backend/`.

Backend endpoint tests use an isolated in-memory SQLite database and do not require or modify the development PostgreSQL database. The current backend tests use Python's standard-library `unittest`, so no additional test dependencies are needed.
