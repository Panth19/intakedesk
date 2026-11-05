# IntakeDesk – AI order and quote intake for Nutrifill

Working-student project for **Care4trade & Nutrifill GmbH** (Griesheim / Frankfurt): merchandise management, purchasing and sales automation, n8n-style workflows, and an Odoo-like ERP draft.

Customer emails and order PDFs (German and English) are extracted into structured line items. High-confidence jobs become **draft quotations in Odoo**. Uncertain jobs go to a **human review queue**. A labelled synthetic corpus replaces model fine-tuning.

## Why this matches the role

| Job task | What this repo does |
| --- | --- |
| Set up and optimize merchandise management | Product master, partners, stock, reorder points, 19% VAT, volume discount |
| Automate purchasing and sales with AI | Extract RFQs/POs, draft sale quotes, emit purchase suggestions when stock dips |
| Intelligent workflows for orders, quotes, purchasing | n8n workflow JSON + FastAPI router with a 0.82 confidence threshold |
| Link software and interfaces | IMAP/PDF → n8n → `/api/webhook/n8n` → Odoo `sale.order` simulation |
| Analyse and document processes | Workflow view, audit log, evaluation dashboard |
| Test automated processes | 12 gold-labelled DE/EN documents, pytest, SKU recall / auto-share / EUR per doc |

Fine-tuning is intentionally **not** used. Live extraction uses a Groq/OpenAI chat model with catalog grounding. A labelled set plus confidence routing measures quality. Cheaper to iterate in a working-student week than a fine-tune.

## Metrics

- **Extraction accuracy** – partner match, SKU recall/precision, quantity accuracy vs gold labels
- **Share handled without review** – jobs that auto-create an Odoo draft
- **Cost per document** – token-cost estimate of the extraction step
- **Routing accuracy** – did the threshold send the right jobs to humans?

## Stack

- **n8n** – mailbox and PDF intake (`n8n/nutrifill_intake_workflow.json`)
- **FastAPI** – extraction, review, Odoo simulation, evaluation
- **Groq GPT-OSS 20B** (or any OpenAI-compatible API) – live document extraction
- **React / Vite** – ops desk (inbox, review, quotations, KPIs, AI settings)
- **Odoo Community (simulated)** – `sale.order` drafts, tax, stock, purchase signals

Production would swap the in-memory Odoo simulator for the Odoo XML-RPC/JSON-2 API (`sale.order`, `res.partner`, `product.product`, `purchase.order`).

## Run locally

```bash
# Backend
cd backend
pip install --break-system-packages -r requirements.txt
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (proxies /api to the backend)
cd frontend
npm install
npm run dev
```

Or `./start.sh` to start both.

Copy `.env.example` and add a Groq key if you want live LLM extraction:

```bash
# USER_LLM_API_KEY=gsk_...
# USER_LLM_ENABLED=true
```

Without a key the app still runs on catalog rules. New documents use the LLM once a key is set in **AI settings** or in env vars.

## Deploy for free

Step-by-step (Render, Railway, Fly, Hugging Face): see `DEPLOY.md`.

Short version: push to GitHub, create a Render Docker web service from `Dockerfile`, set `USER_LLM_API_KEY`.

## Tests

```bash
cd backend
python3 -m pytest -q
```

## API

- `POST /api/ingest` – drop a parsed email/PDF
- `POST /api/webhook/n8n` – same payload from n8n
- `POST /api/jobs/{id}/review` – working-student correction, then Odoo draft
- `POST /api/quotes/{id}/state` – `draft` / `sent` / `sale` / `cancel`
- `GET /api/evaluation` – gold-label metrics

## Domain

Nutritional wholesale (protein, creatine, omega-3, pharmacy essentials) sold to gyms, pharmacies and retailers around Frankfurt–Darmstadt–Mainz. Master data is synthetic.
