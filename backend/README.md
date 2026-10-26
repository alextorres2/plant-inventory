# Backend

## Database setup and migrations

Apply the versioned schema migration before starting the API:

```sh
cd backend
.venv/bin/alembic upgrade head
```

The migration adds photo metadata while retaining existing plant rows. Set `DATABASE_URL` to select a database; the default remains `postgresql://localhost/plant_inventory`. The API no longer creates or upgrades tables at import time.

## Photo uploads

Photo bytes are stored outside PostgreSQL by the `LocalPhotoStorage` adapter. The default directory is `backend/uploads/`, which is ignored by Git. Set `PLANT_UPLOAD_DIR` to use a different local path. Replace this adapter with persistent object storage before deploying to an environment where local files are ephemeral or shared across multiple API instances.

Still-image uploads are limited to 10 MB and validated by decoding their actual contents. Supported formats are JPEG, PNG, WebP, iPhone HEIC/HEIF, AVIF, and MPO stereo JPEG; HEIC/HEIF/AVIF/MPO uploads are converted to a JPEG still (MPO uses the primary frame). iPhone Live Photo `.MOV` clips up to 50 MB are decoded and their first video frame is stored as a JPEG still; the motion is discarded. Other unsupported formats are rejected. Browsers that support `capture="environment"` offer a separate camera action; the existing-photo picker is also available.

## Run API tests

From the `backend` directory, install the backend dependencies and run:

```sh
python -m unittest discover -s tests -v
```

The endpoint tests use Python's built-in `unittest` runner, an in-memory SQLite database, and temporary upload directories, isolated from the configured PostgreSQL development database and local upload folder. They build a small FastAPI app around the plants router. Tests also verify the migration preserves a pre-existing plant record.
