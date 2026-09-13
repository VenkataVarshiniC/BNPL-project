# Deploying Ledger (BNPL backend + frontend)

You'll deploy the backend first (so you have a live API URL), then the frontend
pointed at it. Both platforms below have free tiers and connect directly to GitHub.

## 0. Push your code to GitHub

If you haven't already:

```bash
cd BNPLProject
git init
git add .
git commit -m "Initial commit"
```

Create a new repo on GitHub, then:

```bash
git remote add origin https://github.com/<you>/BNPLProject.git
git branch -M main
git push -u origin main
```

## 1. Deploy the backend — Render

1. Go to https://render.com → sign in with GitHub.
2. **New +** → **Blueprint** → select your repo. Render will detect `backend/render.yaml`
   automatically (point the root directory to `backend/` if asked).
3. Render runs the build command from `render.yaml`, which installs dependencies,
   regenerates the synthetic dataset, and trains the model fresh on Render's own
   Python/scikit-learn versions — this avoids the pickle version-mismatch issue
   you hit locally, since the model is always trained on the same box that serves it.
4. Once deployed, copy your live URL — something like
   `https://bnpl-backend.onrender.com`.
5. Confirm it's up: visit `https://bnpl-backend.onrender.com/docs`.

**Note:** Render's free tier spins down after inactivity — the first request after
idle can take ~30-50 seconds to wake up. Fine for a portfolio demo, worth mentioning
if you're showing it live.

## 2. Deploy the frontend — Vercel

1. Go to https://vercel.com → sign in with GitHub.
2. **Add New** → **Project** → select your repo, set root directory to `frontend/`.
3. Vercel auto-detects Vite. Before deploying, add an environment variable:
   - `VITE_API_BASE_URL` = `https://bnpl-backend.onrender.com` (your Render URL from step 1)
4. Deploy. `vercel.json` is already included so client-side routes (`/app/segmentation`,
   etc.) don't 404 on refresh.
5. You'll get a URL like `https://bnpl-ledger.vercel.app` — that's your shareable link.

## 3. Tighten CORS (optional, recommended before sharing widely)

Right now `backend/app/main.py` allows all origins (`allow_origins=["*"]`), which is
fine for development. Once you have your Vercel URL, lock it down:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bnpl-ledger.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push — Render redeploys automatically on push to `main`.

## 4. Verify end to end

Open your Vercel URL, click through all six pages, and confirm the "API connected"
pill in the top bar goes green. If it stays red, double-check the `VITE_API_BASE_URL`
env var on Vercel matches your Render URL exactly (no trailing slash).
