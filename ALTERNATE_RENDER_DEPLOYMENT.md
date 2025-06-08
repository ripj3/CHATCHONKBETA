# Alternate Render.com Deployment: Separate Frontend and Backend Services

This guide explains how to deploy your Next.js frontend and FastAPI backend as **separate services** on Render.com for improved scalability and faster deployments in production.

---

## 1. Backend (FastAPI)
- **Service Type:** Web Service
- **Root Directory:** `backend/`
- **Build Command:**
  ```sh
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```sh
  python -m uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
- **Environment Variables:**
  - Add all backend-related variables (see `.env` and `render.yaml`).
  - Set `ALLOWED_ORIGINS` to your frontend's Render URL (e.g., `https://your-frontend.onrender.com`).
  - Set `API_URL` and similar variables as needed for production.

---

## 2. Frontend (Next.js)
- **Service Type:** Web Service
- **Root Directory:** `frontend/`
- **Build Command:**
  ```sh
  npm install && npm run build
  ```
- **Start Command:**
  ```sh
  npm start
  ```
- **Environment Variables:**
  - Set all `NEXT_PUBLIC_` variables (see `.env`).
  - Set `NEXT_PUBLIC_API_URL` to your backend's Render URL + `/api` (e.g., `https://your-backend.onrender.com/api`).

---

## 3. CORS & API URLs
- **Backend:**
  - `ALLOWED_ORIGINS` should match your frontend's Render URL.
- **Frontend:**
  - `NEXT_PUBLIC_API_URL` should point to your backend's public API endpoint.

---

## 4. Static Files
- The frontend is served by Next.js, not by FastAPI. Remove or comment out the `app.mount("/", ...)` line in `backend/main.py` if you want to avoid serving static files from the backend.

---

## 5. render.yaml Example (Optional)
You can define both services in a single `render.yaml`:

```yaml
services:
  - type: web
    name: chatchonk-backend
    env: python
    rootDir: backend
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python -m uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: ALLOWED_ORIGINS
        value: "https://your-frontend.onrender.com"
      # ...other backend env vars...

  - type: web
    name: chatchonk-frontend
    env: node
    rootDir: frontend
    buildCommand: "npm install && npm run build"
    startCommand: "npm start"
    envVars:
      - key: NEXT_PUBLIC_API_URL
        value: "https://your-backend.onrender.com/api"
      # ...other frontend env vars...
```

---

## 6. Summary
- **Separate services = faster, more scalable deployments.**
- **Update environment variables to point to the correct URLs.**
- **No need to copy frontend static files to the backend.**

---

For questions or to switch back to single-service, see the main README.
