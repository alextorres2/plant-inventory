# Backend

## Run API tests

From the `backend` directory, install the backend dependencies and run:

```sh
python -m unittest discover -s tests -v
```

The endpoint tests use Python's built-in `unittest` runner and an in-memory SQLite database, isolated from the configured PostgreSQL development database. They build a small FastAPI app around the plants router rather than importing `app.main`, whose startup code creates tables against the configured database. No additional test dependencies are required.
