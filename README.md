# ChatChonk

> **“Tame the Chatter. Find the Signal.”**  
> You enjoy that hyper-focus. **We organize it all.**

ChatChonk is a one-person, privacy-first SaaS that turns messy, ideation-heavy AI chat exports (ChatGPT, Claude, Gemini & more) into **Obsidian- and Notion-ready knowledge bundles**—complete with backlinks, tags, Dataview metadata, and media linking.  
Designed for second-brain builders, neurodivergent thinkers, and anyone who drowns in brilliant but scattered conversations.

---

## ✨ Why It Exists

People with ADHD (like the founder) generate **tons of creative ideas** during AI chat sessions but struggle to retrieve them later. ChatChonk harnesses that chaotic brilliance by:

1. **Ingesting** ZIP archives (up to 2 GB) containing chat logs & media.  
2. **Structuring** content with AI-powered templates optimised for ideation discovery.  
3. **Exporting** polished Markdown/Notion assets that drop straight into your knowledge base.

Enjoy the hyperfocus—ChatChonk does the filing.

---

## 🗺 Project Structure

```
chatchonk/
  backend/          # FastAPI  · Python 3.11 · Supabase client
  frontend/         # Next.js 14 · App Router · Tailwind CSS
  templates/        # YAML templates (ADHD-optimised)
  scripts/          # Helper & deploy scripts
  docs/             # Additional docs / ADRs
```

Core flow: `Upload → ZIP & Media Parse → AI Analysis (AutoModel) → Template Apply → Export`.

---

## ⚙️ Local Setup

### 1. Clone & prerequisites

```bash
git clone https://github.com/yourname/chatchonk.git
cd chatchonk
```

*Requirements:*  
- Python 3.11+  
- Node.js 18+ (with npm or pnpm)  
- Supabase account (tables already provisioned)  
- (Optional) ffmpeg & tesseract for rich media extraction

### 2. Environment variables

Create `.env` in project root:

```env
# ==== Supabase ====
SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_ANON_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_SERVICE_ROLE_KEY=xxxxxxxxxxxxxxxx

# ==== Backend secrets ====
CHONK_SECRET_KEY=change_me
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx      # initial AI provider
OPENAI_API_KEY=sk-xxxxxxxx (optional)
ANTHROPIC_API_KEY=claude-xxxxxxxx (optional)

# ==== File processing ====
UPLOAD_DIR=./uploads
TEMP_DIR=./tmp

# ==== App ====
ALLOWED_ORIGINS=http://localhost:3000
PORT=8000
```

### 3. Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install          # or pnpm i
npm run dev          # http://localhost:3000
```

The app will proxy API requests to `localhost:8000`.

---

## 🛠 Development Workflow

| Task | Command |
|------|---------|
| Start backend (hot-reload) | `uvicorn backend.main:app --reload` |
| Start frontend | `npm run dev` |
| Lint & format | `ruff check`, `black .`, `eslint .` |
| Run unit tests | `pytest` |
| Generate template docs | `python scripts/template_preview.py` |

Feature branches follow **conventional commits** + PR review.

---

## 🚀 Deployment (Digital Ocean Droplet)

Traditional (non-Docker) flow—perfect for lightweight VPS.

1. **Provision droplet** – Ubuntu 22.04, 2 vCPU / 2 GB RAM.  
2. **SSH & setup**  

```bash
# system packages
sudo apt update && sudo apt install python3.11-venv nodejs npm nginx git
# optional media tools
sudo apt install ffmpeg tesseract-ocr
```

3. **Clone repo & build**

```bash
git clone https://github.com/yourname/chatchonk.git /opt/chatchonk
cd /opt/chatchonk
# backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
# frontend
cd frontend && npm ci && npm run build
```

4. **Process manager**

Using **PM2**:

```bash
sudo npm i -g pm2
pm2 start backend/pm2.backend.json    # uvicorn
pm2 start frontend/pm2.frontend.json  # next start
pm2 save
pm2 startup
```

5. **nginx reverse proxy**

```nginx
server {
  server_name chatchonk.com;
  location /api/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
  }
  location / {
    proxy_pass http://localhost:3000;
    proxy_set_header Host $host;
    try_files $uri $uri/ /index.html;
  }
}
```

6. **SSL** – issue cert via Cloudflare or `certbot`.

---

## 🏗 Architecture Overview

| Layer | Tech | Notes |
|-------|------|-------|
| Frontend | Next.js 14, Tailwind, Brand Kit | Responsive, accessible UI |
| Backend | FastAPI, Pydantic | Stateless API, JWT (future) |
| AI Layer | AutoModel (HuggingFace MVP) | Pluggable providers (OpenAI, Anthropic…) |
| Data | Supabase Postgres | Auth, storage, edge functions |
| Processing | Async ZIP parser + media extractors | Streams >2 GB w/ chunk uploads |
| Exports | Markdown / Notion JSON | Obsidian-ready, full linking |

Supabase **Edge Functions** will replace heavy Celery queues for background tasks.

---

## 🎨 Brand Integration Notes

* **Colors** – Imported via `tailwind.config.js` under `colors.chatchonk`.  
* **Fonts** – Inter (body) & Poppins (headings) loaded in `_app.tsx`.  
* **Components** – Re-usable `<Button>`, `<Card>`, `<Logo>` leverage brand classes (`btn-primary`, `card`, etc.).  
* **CTA Section** appears on landing page hero with gradient background `gradient-primary`.  
* **Accessibility** – All interactive elements meet WCAG 2.1 AA contrast; `focus-brand` utility added.  
* **Tone** – Playful yet professional copy; always reference benefit to hyper-focused creators.  

---

## 🤝 Contributing

Early *dog-fooding* is welcome—open issues for any pain-points, especially around ADHD usability or new chat export formats.

---

## 📜 License

None — at this time
Built with 🐱‍👓 & ☕ by Rip Jonesy.
