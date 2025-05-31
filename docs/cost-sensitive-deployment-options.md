# Cost-Sensitive Beta Deployment Options (≈120 Users)

_Target stack: FastAPI backend · Next.js frontend · Supabase (Postgres + Storage + Edge Functions)_

Large uploads (≤ 2 GB) are **always** sent **directly from the browser to Supabase Storage** with signed URLs.  
The backend is then notified to start processing, so the compute platform never sees multi-gigabyte files.

---

## Option A · **Vercel (Frontend) + Fly.io (Backend)**

| Component | Platform / Plan | Monthly Cost |
|-----------|-----------------|-------------|
| Next.js frontend | Vercel **Hobby** (free) | **$0** |
| FastAPI backend | Fly.io **512 MB shared-CPU** instance | **$5** |
| Supabase | `free` project (0.5 GB DB / 1 GB Storage / 2 GB egress) | **$0** → upgrade when limits hit |
| _Estimated total_ |  | **≈ $5 / month** |

### Pros
- Vercel Hobby = zero-config Next.js deploys + global CDN.
- Fly.io tiny instance is enough for I/O-bound FastAPI (API calls & small JSON).
- Both support GitHub Actions for CI/CD.
- Can scale Fly.io to 1 GB RAM (+$2) if API memory spikes.

### Cons
- Fly.io free bandwidth is limited (160 GB); heavy API traffic may incur ~$0.02/GB overage.
- Cold starts possible on Fly.io shared VM if idle.
- Supabase free tier storage/egress small; may need **$25** “Pro” upgrade if users store lots of media.

### File-Upload Flow
1. Frontend requests signed upload URL from Supabase Edge Function.  
2. Uppy uploads the 2 GB ZIP **directly to Supabase Storage** in 5–10 MB chunks (tus.js).  
3. After “upload-complete” webhook, Edge Function enqueues background task or notifies FastAPI via HTTP to start parsing.

---

## Option B · **Render (all-in-one) + Supabase**

| Component | Platform / Plan | Monthly Cost |
|-----------|-----------------|-------------|
| Next.js (static) | Render **Static Site** (free, 100 GB CDN) | **$0** |
| FastAPI backend | Render **Background Worker** (`starter`, 512 MB RAM) | **$7** |
| Supabase | free → Pro later | **$0** |
| _Estimated total_ |  | **≈ $7 / month** |

### Pros
- Single provider for both services; simple dashboard.
- Free static site automatically rebuilds on Git pushes.
- Background Worker plan sleeps after 15 min idle but _queues_ requests and wakes quickly.
- Automatic HTTPS, PR previews, cron jobs.

### Cons
- Cold-start latency (a few seconds) when the worker wakes.
- Needs custom Render blueprint YAML; slightly more DevOps than Vercel.
- Free static site bandwidth capped at 100 GB/month (should be fine for 120 users).

### File-Upload Flow
Same direct-to-Supabase approach. Worker only fetches the file via Supabase signed URL _after_ upload completes.

---

## Option C · **Oracle Cloud Free Tier (Always-Free Arm VM)**

| Component | Platform / Plan | Monthly Cost |
|-----------|-----------------|-------------|
| Arm VM (4 vCPU, 24 GB RAM, 200 GB SSD) | Oracle “Always Free” | **$0** |
| Setup | nginx reverse proxy, PM2, FastAPI & Next.js both on same VM | **$0** |
| Supabase | free → Pro when necessary | **$0** |
| _Estimated total_ |  | **$0 / month** |

### Pros
- **Truly free** compute with surprisingly good specs.
- Enough RAM/CPU headroom for beta + small Celery worker if needed.
- Full root access → easiest to replicate local dev setup.
- One place to run cron, background tasks, monitoring.

### Cons
- Limited regional availability; signup queue.  
- No built-in autoscaling—manual resize or move when you outgrow free tier.
- Must manage SSL, firewall, updates yourself (standard VPS duties).
- Ingress bandwidth free, egress limited to 10 TB/month (fine for beta).

### File-Upload Flow
- Browser uploads directly to Supabase Storage.  
- VM processes via signed URL; no 2 GB files hit Oracle bandwidth.

---

## Cost Summary

| Option | Est. Monthly Cost | Good For |
|--------|------------------|----------|
| **A · Vercel + Fly.io** | **$5** | Fastest setup, zero DevOps, tiny budget. |
| **B · Render** | **$7** | One-dashboard simplicity; still cheap. |
| **C · Oracle Free Tier** | **$0** | Maximum cost-saving if you’re comfortable managing a VPS. |

All three options keep **Supabase** as the heavy-lifting backbone (Postgres, Storage, Edge Functions) and push 2 GB uploads directly from client → Supabase, minimizing compute costs.

Choose the one that best matches your comfort level with DevOps and how quickly you want to iterate.

---
