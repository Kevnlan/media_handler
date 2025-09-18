# Media Handler (Backend + Auth)

A small Django-based monorepo containing two services:

- auth_server — authentication service (JWT issuance, registration, profile, logout)
- backend_server — media service (images, videos, audios and collections)

This README explains repository structure, setup, running the two services, environment variables, and available API endpoints.

---

## Repository structure (top-level)

- `auth_server/` — Django project that provides user registration, login (JWT tokens), profile and logout endpoints.
- `backend_server/` — Django project that provides media handling API (media records and collections). Uses JWTs issued by `auth_server` for authentication.
- `media/` — folders used by the backend to store media files (audio/images/videos) during development.

Project apps:

- `auth_server/accounts` — custom user model, serializers and auth endpoints.
- `backend_server/media_handler` — Media and Collection models, serializers, views, and JWT auth bridge.

---

## Requirements

- Python 3.8+
- PostgreSQL (or adjust `DATABASES` settings to use SQLite for quick dev)
- Recommended: virtualenv or venv

There should be a `requirements.txt` at the repo root. Install packages into a virtual environment.

---

## Quick setup (development)

1. Clone the repository

```bash
git clone https://github.com/Kevnlan/media_handler.git
cd media_handler
```

2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

Create a `.env` file at the project root (or export environment variables). At minimum set the JWT signing key and DEBUG for local dev. Example `.env` contents:

```env
# Shared JWT signing key used by both services (change to a secure, random value in prod)
JWT_SIGNING_KEY=your_super_secret_signing_key_here

# Django debug
DEBUG=True

# Optionally override DB credentials or SECRET_KEY per service
# AUTH_DB_NAME=auth_db
# BACKEND_DB_NAME=backend_db
```

Note: Each Django settings file reads a variable named `JWT_SIGNING_KEY` and assigns it to SIMPLE_JWT.SIGNING_KEY. Ensure both services use the same signing key so tokens from `auth_server` validate in `backend_server`.

5. Apply migrations (for each service)

```
# Auth service
cd auth_server
python manage.py makemigrations
python manage.py migrate

# Backend service
cd ../backend_server
python manage.py makemigrations
python manage.py migrate
```

6. Run the application

## Deployment Options

### 🚀 Option 1: API Gateway (Recommended for Mobile Testing)
**Single endpoint for easy mobile app integration**

```bash
# Start all services with unified API Gateway
./run_with_gateway.sh
```

**Access Points:**
- **API Gateway:** `http://localhost:3000` (Single endpoint for all APIs)
- **Mobile Testing:** `http://YOUR_COMPUTER_IP:3000` 
- **Health Check:** `http://localhost:3000/health`

**API Endpoints:**
- Authentication: `http://localhost:3000/api/auth/`
- Media/Backend: `http://localhost:3000/api/media/`

### 🔧 Option 2: Separate Services (Development)
```bash
# Quick start script for both servers
./run_local.sh

# Or manually:
cd auth_server && python manage.py runserver 8000 &
cd backend_server && python manage.py runserver 8001 &
```

**Access Points:**
- Auth server: `http://localhost:8000`
- Backend server: `http://localhost:8001`

### 🌐 Option 3: Production with Nginx
```bash
# One-time setup
./setup_nginx.sh

# Then run Django services
./run_local.sh
```

**Production Access:**
- Single endpoint: `http://localhost/api/auth/` and `http://localhost/api/media/`

### 🐳 Option 4: Docker Deployment
```bash
docker-compose up
```

Adjust ports as needed. Both services must be running and reachable during integration testing.

---

## Configuration notes

- Signing key:
  - `auth_server/auth_server/settings.py` and `backend_server/backend_server/settings.py` both use a variable `JWT_SIGNING_KEY` and set it as `SIMPLE_JWT['SIGNING_KEY']`.
  - In production, keep the signing key secret and rotate carefully.

- CORS and allowed hosts:
  - `backend_server` currently allows all origins (CORS_ALLOW_ALL_ORIGINS = True) — restrict this in production.

- Authentication bridging:
  - `backend_server/media_handler/auth.py` contains a lightweight JWTAuthentication implementation that decodes tokens using the signing key specified in `SIMPLE_JWT['SIGNING_KEY']`. The authentication returns a simple user-like object with `id` and `email` fields (no local DB user required).

---

## API reference

Authentication (auth_server)

- POST /api/auth/register/ — register a new user (public)
  - Body fields (from serializer): `first_name`, `last_name`, `email`, `username`, `phone_number`, `password`.

- POST /api/auth/login/ — obtain JWTs (access + refresh)
  - Provide credentials (username/email and password). Response contains `access` and `refresh` tokens.

- POST /api/auth/token/refresh/ — refresh access token using refresh token

- GET /api/auth/profile/ — get current user profile (requires Authorization header)

- POST /api/auth/logout/ — blacklist refresh token (requires Authorization header)

Using tokens with the backend (backend_server)

- All media backend endpoints require a valid access token in the Authorization header:

  Authorization: Bearer <access_token>

Media endpoints (backend_server)

Base path: /api/media/

- GET /api/media/media/  — list media items. Supports query params:
  - `type` — one of `image`, `video`, `audio` (filter by media type)
  - `search` — search on `name` and `description`
  - pagination: `page` and `page_size` (defaults to 10 items per page)

- POST /api/media/media/ — create a media record (authenticated)

- GET /api/media/media/<id>/ — retrieve a single media record

- PUT /api/media/media/<id>/ — update media record

- DELETE /api/media/media/<id>/ — soft-delete (sets `is_deleted=True`)

- POST /api/media/media/<id>/add-to-collection/ — add this media to a collection. Body: `{ "collection_id": "<collection_uuid>" }`. The authenticated user must own both the media and the collection.

- POST /api/media/media/<id>/remove-from-collection/ — remove this media from its collection (no body required). The authenticated user must own the media.

Collections endpoints

- GET /api/media/collections/ — list collections owned by the authenticated user
- POST /api/media/collections/ — create a new collection
- GET /api/media/collections/<id>/ — retrieve collection with included media
- PUT /api/media/collections/<id>/ — update collection
- DELETE /api/media/collections/<id>/ — delete collection

Notes:
- The media model stores `user` as an integer (user id from the auth service) and the backend enforces that users only see their own media by filtering on `user=self.request.user.id`.
- The router registers `media` and `collections` viewsets under the `media_handler` app, so the final paths are prefixed with `/api/media/` by the project URL configuration.

---

## Example flows (high level)

1. Register a user via `auth_server`.
2. Login to obtain an access token.
3. Use that access token to create/list media and collections on `backend_server`.

Example HTTP usage (replace host/port accordingly):

- Obtain tokens: POST `http://localhost:8000/api/auth/login/` with credentials — receive `access` and `refresh`.
- Call backend: GET `http://localhost:8001/api/media/media/?type=image` with header `Authorization: Bearer <access>`.

---

## Development tips

- If you want a single signing key across both services, set the same `JWT_SIGNING_KEY` environment variable for both.
- For quick local development without Postgres, update each project's `DATABASES` setting to use SQLite (or create separate Docker Compose with Postgres containers).
- Consider adding `django-environ` or similar to load `.env` files into Django settings safely.

---

## Testing

- Each Django project contains `manage.py` and its own tests module. Run tests per project:

```
# in project folder (auth_server or backend_server)
python manage.py test
```

---

## Security & production considerations

- Never commit production signing keys or Django SECRET_KEY to version control.
- Use HTTPS in production and set appropriate CORS/ALLOWED_HOSTS.
- Rotate JWT signing keys carefully (support old tokens or require re-login on rotation).

---

## Example curl commands

Below are small curl examples that demonstrate common flows between `auth_server` (port 8000) and `backend_server` (port 8001). Replace host/port and payloads as needed.

1) Register a new user

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Jane","last_name":"Doe","email":"jane@example.com","username":"jane","phone_number":"+1234567890","password":"strongpassword"}'
```

2) Login (obtain access & refresh tokens)

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"jane","password":"strongpassword"}'

# Response contains {"access": "<access_token>", "refresh": "<refresh_token>"}
```

3) Refresh access token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}'
```

4) Get user profile (auth server)

```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```

5) Create a media record (backend server)

```bash
curl -X POST http://localhost:8001/api/media/media/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"name":"my-photo.jpg","type":"image","size":12345,"storage_path":"/media/images/my-photo.jpg","description":"Vacation photo"}'
```

6) List media (filter by type)

```bash
curl -X GET "http://localhost:8001/api/media/media/?type=image&page=1&page_size=10" \
  -H "Authorization: Bearer <access_token>"
```

7) Logout (blacklist refresh token)

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"refresh":"<refresh_token>"}'
```

---

## Media storage (development)

The backend server stores uploaded media files under `backend_server/media/` (configured via `MEDIA_ROOT` in `backend_server/backend_server/settings.py`). This repository already contains subfolders:

- `backend_server/media/images/`
- `backend_server/media/videos/`
- `backend_server/media/audio/`

Uploaded files will be placed under `backend_server/media/uploads/YYYY/MM/DD/` by default. You can change `upload_to` in `media_handler.models.Media.file` if you want a different path.

Example curl (multipart) to upload a file and save to repo media folder:

```bash
curl -X POST http://localhost:8001/api/media/ \
  -H "Authorization: Bearer <access_token>" \
  -F "name=my-photo.jpg" \
  -F "type=image" \
  -F "file=@/path/to/my-photo.jpg"
```

After upload, file will be available at `backend_server/media/uploads/YYYY/MM/DD/<filename>` and the `storage_path` field will contain the relative storage path.

---

## .env.example

A minimal `.env.example` is included in the repository root. Copy it to `.env` and update values for your environment. It demonstrates the shared JWT signing key and optional DB overrides.

Example `.env.example` contents:

```env
# Shared signing key for JWTs (change for production)
JWT_SIGNING_KEY=replace_with_a_secure_random_value

# Django debug mode (True for local development)
DEBUG=True

# Optional DB overrides (if you prefer to set via env vars)
AUTH_DB_NAME=auth_db
AUTH_DB_USER=django_user
AUTH_DB_PASSWORD=password
AUTH_DB_HOST=localhost
AUTH_DB_PORT=5432

BACKEND_DB_NAME=backend_db
BACKEND_DB_USER=django_user
BACKEND_DB_PASSWORD=password
BACKEND_DB_HOST=localhost
BACKEND_DB_PORT=5432

# Optional: override SECRET_KEY for each service (recommended in prod)
# AUTH_SECRET_KEY=your_auth_secret_key
# BACKEND_SECRET_KEY=your_backend_secret_key
```

---
