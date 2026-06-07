#!/bin/bash
set -e

echo "📥 Pulling latest code from GitHub..."
cd ~/DocXtract/backend

git fetch origin
git reset --hard origin/main

echo "🐳 Rebuilding and restarting containers..."
docker compose down
docker compose up -d --build

echo "✅ Deployment complete!"

