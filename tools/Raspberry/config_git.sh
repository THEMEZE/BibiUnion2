#!/bin/bash
set -e

echo "==== 1. Installation Git (si besoin) ===="
sudo apt update
sudo apt install git -y

echo "==== 2. Configuration identité Git ===="

CURRENT_NAME=$(git config --global user.name || true)
CURRENT_EMAIL=$(git config --global user.email || true)

if [ -n "$CURRENT_NAME" ] || [ -n "$CURRENT_EMAIL" ]; then
    echo "⚠️ Configuration Git existante détectée :"
    echo "   name : $CURRENT_NAME"
    echo "   email: $CURRENT_EMAIL"

    read -p "❓ Voulez-vous l'écraser ? (y/N) : " confirm

    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "✔ Conservation de la configuration existante"
    else
        git config --global user.name "THEMEZE_RP"
        git config --global user.email "guillaume.themeze@gmail.com"
        echo "✔ Configuration Git mise à jour"
    fi
else
    git config --global user.name "THEMEZE_RP"
    git config --global user.email "guillaume.themeze@gmail.com"
    echo "✔ Configuration Git initialisée"
fi

echo "==== 3. SSH Setup ===="

SSH_KEY="$HOME/.ssh/id_ed25519"

if [ -f "$SSH_KEY" ]; then
    echo "⚠️ Clé SSH déjà existante : $SSH_KEY"

    read -p "❓ Voulez-vous la remplacer ? (y/N) : " confirm

    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "✔ Conservation de la clé SSH existante"
    else
        echo "🗑 Suppression ancienne clé..."
        rm -f "$SSH_KEY" "$SSH_KEY.pub"

        ssh-keygen -t ed25519 -C "raspberry" -f "$SSH_KEY" -N ""
        echo "✔ Nouvelle clé SSH générée"
    fi
else
    echo "🔐 Génération clé SSH..."
    ssh-keygen -t ed25519 -C "raspberry" -f "$SSH_KEY" -N ""
    echo "✔ Clé SSH créée"
fi

echo "==== 4. Activation agent SSH ===="
eval "$(ssh-agent -s)"
ssh-add "$SSH_KEY"

echo "==== 5. Clé publique (à copier sur GitHub) ===="
echo ""
cat "$SSH_KEY.pub"
echo ""

echo "==== 6. Instructions GitHub ===="
echo "👉 GitHub → Settings → SSH and GPG keys"
echo "👉 New SSH Key"
echo ""

echo "==== 7. Test (manuel après ajout GitHub) ===="
echo "ssh -T git@github.com"

