# Login 500 Fix

## Problem
Login was returning `500 INTERNAL SERVER ERROR` because the backend was trying to connect to MySQL on `127.0.0.1:3306` with no password.

The working local database for this project is currently:

- **Host:** `127.0.0.1`
- **Port:** `3307`
- **User:** `root`
- **Password:** empty
- **Database:** `library_system_v2`

## Permanent Fix Applied
The app config now defaults to port `3307`, and `run.ps1` also starts the backend with `DB_PORT=3307`.

If login fails again, check `backend/backend.log`. Database connection problems should now return a clear `503` message instead of a vague login `500`.

## Verify
Run:

```powershell
python backend/run_server.py
```

Then open:

```text
http://localhost:5000/login
```
