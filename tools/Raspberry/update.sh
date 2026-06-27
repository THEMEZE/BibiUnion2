#!/bin/bash
set -e

cd /mnt/mariage_data/

echo "Quel dépôt veux-tu utiliser ?"
echo "  1) BibiUnion"
echo "  2) BibiUnion2"
read -p "Choix (1 ou 2) : " choice

if [ "$choice" = "1" ]; then
    REPO="https://github.com/THEMEZE/BibiUnion.git"
elif [ "$choice" = "2" ]; then
    REPO="https://github.com/THEMEZE/BibiUnion2.git"
else
    echo "❌ Choix invalide"
    exit 1
fi

if [ -d "BibiUnion/.git" ]; then
    echo "📥 Dépôt existant"

    cd BibiUnion

    git remote set-url origin "$REPO"

    echo "Synchronisation avec GitHub..."

    git fetch origin
    git reset --hard origin/main

    # on conserve index.html local si nécessaire
    git checkout --ours index.html 2>/dev/null || true

    echo "✔ Projet mis à jour."

else
    echo "📥 Premier téléchargement..."

    git clone "$REPO" BibiUnion
    cd BibiUnion

    echo "✔ Clone terminé."
fi
