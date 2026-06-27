#!/bin/bash
set -e

echo "📥 Récupération de index.html..."
git fetch origin
git restore --source origin/main index.html 2>/dev/null || true

echo "📤 Envoi vers GitHub..."
git add .

git commit -m "${1:-Mise à jour}" || true

git push origin main
