# Local Deployment Guide (No Docker)

This guide explains how to run ChatChonk (FastAPI backend + Next.js frontend) locally on a Windows laptop without Docker. This is ideal for older hardware like the ASUS G75V.

---

## 1. Prerequisites
- **Python 3.9+** (Install from https://www.python.org/downloads/)
- **Node.js 18+** (Install from https://nodejs.org/)
- **PowerShell** (default on Windows 10/11)
- **Git** (optional, for code updates)

---

## 2. Clone the Repository
If you haven't already:
```pwsh
git clone <your-repo-url>
cd B15B_CHATCHONK7
```

---

## 3. Set Up Environment Variables
- Copy `env.example` to `.env` and fill in required values (API keys, secrets, etc.).
- Or, set environment variables directly in your system if you prefer.

---

## 4. Build and Prepare the Frontend
Run the provided PowerShell script:
```pwsh
./build_and_copy_frontend.ps1
```
This will:
- Build the Next.js frontend
- Export static files
- Copy them to `frontend_build/` for the backend to serve
- Install backend Python dependencies

---

## 5. Run the Backend (FastAPI)
Start the FastAPI backend (serves both API and frontend):
```pwsh
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
```
- The app will be available at: http://localhost:8080
- API docs: http://localhost:8080/api/docs
- Frontend: http://localhost:8080

---

## 6. (Optional) Run Frontend and Backend Separately
If you want hot-reload for frontend development:

**Start Backend:**
```pwsh
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
```

**Start Frontend (in another terminal):**
```pwsh
cd frontend
npm run dev
```
- The frontend will be at http://localhost:3000
- Set `NEXT_PUBLIC_API_URL` in `.env` to `http://localhost:8080/api`
- Set `ALLOWED_ORIGINS` in `.env` to `http://localhost:3000`

---

## 7. Troubleshooting
- If you get errors about missing modules, run `pip install -r backend/requirements.txt` and `npm install` in `frontend/`.
- If ports are in use, change the `--port` argument.
- For CORS errors, check your `.env` settings for `ALLOWED_ORIGINS` and `NEXT_PUBLIC_API_URL`.

---

## 8. Updating the App
- Pull latest code: `git pull`
- Re-run `./build_and_copy_frontend.ps1` after frontend changes.

---

## 9. Notes for Older Laptops
- Close other heavy apps for best performance.
- If you run out of memory, try running only backend or frontend at a time.
- You do **not** need Docker for this workflow.

---

For more advanced deployment (Docker, Render.com, etc.), see the main `README.md` and other deployment docs.
