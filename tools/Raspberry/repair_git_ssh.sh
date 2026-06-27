#!/bin/bash
set -e

echo "========================================="
echo "   Diagnostic Git / GitHub SSH"
echo "========================================="

echo ""
echo "1. Utilisateur courant"
whoami

echo ""
echo "2. Dépôt Git"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "✔ Dépôt Git détecté"
else
    echo "❌ Ce dossier n'est pas un dépôt Git."
    exit 1
fi

echo ""
echo "3. Remote"
git remote -v

echo ""
echo "4. Configuration Git"
echo "Nom   : $(git config --global user.name || echo '<non défini>')"
echo "Email : $(git config --global user.email || echo '<non défini>')"

echo ""
echo "5. Clés SSH"

if [ -f ~/.ssh/id_ed25519 ]; then
    echo "✔ Clé privée trouvée"
else
    echo "❌ ~/.ssh/id_ed25519 absente"
    exit 1
fi

if [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✔ Clé publique trouvée"
else
    echo "❌ ~/.ssh/id_ed25519.pub absente"
    exit 1
fi

echo ""
echo "6. Démarrage ssh-agent"
eval "$(ssh-agent -s)" >/dev/null
ssh-add ~/.ssh/id_ed25519 >/dev/null

echo "✔ Clé chargée"

echo ""
echo "7. Test GitHub"
echo "-----------------------------------------"

set +e
OUTPUT=$(ssh -T git@github.com 2>&1)
STATUS=$?
set -e

echo "$OUTPUT"

echo "-----------------------------------------"

if echo "$OUTPUT" | grep -q "successfully authenticated"; then
    echo ""
    echo "✅ Authentification GitHub OK"
else
    echo ""
    echo "❌ GitHub refuse la clé SSH."
    echo ""
    echo "Ajoute cette clé dans :"
    echo "https://github.com/settings/keys"
    echo ""
    cat ~/.ssh/id_ed25519.pub
    exit 1
fi

echo ""
echo "8. Test du dépôt"

git ls-remote origin >/dev/null

echo "✅ Le dépôt est accessible."

echo ""
echo "========================================="
echo "Configuration Git OK"
echo "========================================="
