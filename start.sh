#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Start FastAPI intake service
cd "$ROOT/backend"
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Start Vite dashboard (exposed preview port)
cd "$ROOT/frontend"
npm run dev

trap "kill $BACKEND_PID" EXIT
