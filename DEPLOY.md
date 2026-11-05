# Deploy IntakeDesk for free

One Docker image serves the React UI and FastAPI. Put your LLM key in environment variables. Never commit it.

## 1. Get a free Groq key (required for live AI)

1. Open https://console.groq.com/keys
2. Sign up with email or Google
3. Click **Create API Key**
4. Copy the key (starts with `gsk_`)
5. Keep it off GitHub

Groq free tier is enough for this demo (GPT-OSS 20B). OpenAI works too but is not free.

Without a key the app still runs: extraction falls back to catalog rules. New messy emails need the key.

## 2. Push the repo to GitHub

```bash
git add .
git commit -m "feat: AI order intake desk with Groq extraction"
git remote add origin https://github.com/YOUR_USER/intakedesk.git
git push -u origin main
```

## 3. Deploy on Render (recommended free host)

1. Open https://render.com and sign in with GitHub
2. **New +** → **Web Service** → connect the GitHub repo
3. Settings:

   - Runtime: **Docker**
   - Dockerfile path: `Dockerfile`
   - Instance: **Free**
   - Health check path: `/api/health`

4. Environment variables:

   | Key | Value |
   | --- | --- |
   | `USER_LLM_ENABLED` | `true` |
   | `USER_LLM_PROVIDER` | `groq` |
   | `USER_LLM_API_KEY` | `gsk_...` (your key) |
   | `USER_LLM_BASE_URL` | `https://api.groq.com/openai/v1` |
   | `USER_LLM_MODEL` | `openai/gpt-oss-20b` |

5. Create Web Service and wait for the first build (3–6 min)
6. Open `https://intakedesk-xxxx.onrender.com`
7. Go to **AI settings** → Test extraction
8. Go to **New document**, paste a German email, run extraction

Free Render apps sleep after ~15 min idle. First request after sleep can take 30–60 s.

You can also click **New Blueprint** and point it at `render.yaml`. You still paste `USER_LLM_API_KEY` by hand.

## 4. Alternative: Railway

1. Open https://railway.app → New Project → Deploy from GitHub
2. Railway detects the Dockerfile
3. Variables → add the same `USER_LLM_*` keys as above
4. Settings → generate a public domain

Railway trial credit is enough for a portfolio demo.

## 5. Alternative: Fly.io

```bash
# Install flyctl, then:
fly launch --dockerfile Dockerfile --no-deploy
fly secrets set USER_LLM_ENABLED=true USER_LLM_PROVIDER=groq USER_LLM_API_KEY=gsk_... USER_LLM_BASE_URL=https://api.groq.com/openai/v1 USER_LLM_MODEL=openai/gpt-oss-20b
fly deploy
```

## 6. Alternative: Hugging Face Spaces (Docker)

1. Create a Space, SDK = Docker
2. Push this repo
3. Space settings → Secrets → `USER_LLM_API_KEY` and the other `USER_LLM_*` values
4. App listens on `$PORT` (already handled in the Dockerfile)

## 7. Run the image locally before you deploy

```bash
docker build -t intakedesk .
docker run --rm -p 8000:8000 \
  -e USER_LLM_ENABLED=true \
  -e USER_LLM_PROVIDER=groq \
  -e USER_LLM_API_KEY=gsk_your_key \
  -e USER_LLM_BASE_URL=https://api.groq.com/openai/v1 \
  -e USER_LLM_MODEL=openai/gpt-oss-20b \
  intakedesk
```

Open http://localhost:8000

## 8. What to paste in the UI if you skip env vars

On a running instance: **AI settings**

- Provider: Groq
- API key: your `gsk_...`
- Save → Test extraction

UI-saved keys live only in process memory. They disappear on restart. Env vars survive restarts. Use env vars on Render.

## 9. Should you add API keys?

Yes, for live AI. Use **your** Groq key, not a platform key.

- Put it in host env vars (`USER_LLM_API_KEY`)
- Or paste it in AI settings for a session
- Do not write it into source, README, or screenshots
- Seeded evaluation still uses rules so the KPI page stays stable and cheap

OpenAI is optional (`gpt-4o-mini`). Groq is the free default.

## 10. After it is live

Share the Render URL in the application. Demo path:

1. Overview KPIs
2. Inbox (seeded DE/EN mails)
3. Review queue
4. Odoo quotes + purchasing suggestions
5. AI settings + New document with a messy email
6. Evaluation vs gold labels
