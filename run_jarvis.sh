#!/usr/bin/env bash
echo "====================================================================="
echo "  INITIALIZING J.A.R.V.I.S. AI SCREEN SYSTEM // STARK HUD"
echo "====================================================================="
if [ ! -d "venv" ]; then
    echo "[1/3] Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "[2/3] Installing dependencies..."
pip install -r requirements.txt --quiet
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[INFO] Created .env from .env.example"
fi
echo "[3/3] Starting J.A.R.V.I.S. HUD Server on http://127.0.0.1:5000 ..."
(sleep 2 && xdg-open http://127.0.0.1:5000 2>/dev/null || open http://127.0.0.1:5000 2>/dev/null) &
python3 app.py
