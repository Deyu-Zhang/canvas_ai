#!/bin/bash

echo "========================================"
echo "Canvas AI Agent - Quick Start"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "[1/4] Checking backend dependencies..."
pip3 install -r requirements.txt --quiet

echo "[2/4] Checking frontend..."
if [ ! -d "frontend/build" ]; then
    echo "[WARNING] Frontend not built."
    echo ""
    echo "To build frontend:"
    echo "  cd frontend"
    echo "  npm install"
    echo "  npm run build"
    echo ""
fi

echo "[3/4] Starting server..."
echo ""
echo "========================================"
echo "Server Options:"
echo "========================================"
echo ""
echo "[1] Local only (http://localhost:8000)"
echo "[2] With LocalTunnel (public access)"
echo ""
read -p "Choose option (1 or 2): " CHOICE

if [ "$CHOICE" == "2" ]; then
    echo ""
    echo "Starting with LocalTunnel..."
    python3 start_server.py
else
    echo ""
    echo "Starting local server only..."
    python3 api_server.py
fi

