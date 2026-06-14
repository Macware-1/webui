#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "[dev] Starting mock backend (Docker)…"
docker compose up -d --build

echo "[dev] Waiting for mock to be ready…"
for i in $(seq 1 20); do
    curl -sf http://localhost:3001/api/info > /dev/null 2>&1 && break
    sleep 1
done

echo "[dev] Starting Vue dev server…"
npm run dev
