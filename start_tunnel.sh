#!/bin/bash
# ============================================================
# start_tunnel.sh — Lance le tunnel Cloudflare et met à jour :
#   - mariage/settings.py (ALLOWED_HOSTS, CSRF, SITE_PUBLIC_URL)
#   - GitHub Pages de redirection (optionnel, via GITHUB_TOKEN)
#   - QR Code
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETTINGS="$SCRIPT_DIR/mariage/settings.py"

# ── Variables GitHub Pages (optionnel) ────────────────────────────────────────
# Pour activer : exporter ces variables avant de lancer le script, ou les
# renseigner ici directement.
#
#   GITHUB_TOKEN      : token personnel GitHub (scope : repo ou contents:write)
#   GITHUB_REPO       : format "utilisateur/nom-repo"  ex: THEMEZE/mariage-redirect
#   GITHUB_PAGES_FILE : fichier à mettre à jour        ex: index.html
#
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_REPO="${GITHUB_REPO:-}"
GITHUB_PAGES_FILE="${GITHUB_PAGES_FILE:-index.html}"

# ── Démarrage du tunnel ───────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    Démarrage du tunnel Cloudflare ...    ║"
echo "╚══════════════════════════════════════════╝"

cloudflared tunnel --url http://localhost:80 2>&1 &
TUNNEL_PID=$!

# ── Attente de l'URL ──────────────────────────────────────────────────────────
URL=""
echo "⏳ En attente de l'URL du tunnel..."
RETRIES=0
while [ -z "$URL" ] && [ $RETRIES -lt 30 ]; do
    sleep 3
    URL=$(curl -s http://127.0.0.1:20241/metrics 2>/dev/null \
        | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1)
    RETRIES=$((RETRIES + 1))
done

if [ -z "$URL" ]; then
    echo "❌ Impossible d'obtenir l'URL du tunnel après 90s. Vérifiez cloudflared."
    kill $TUNNEL_PID 2>/dev/null
    exit 1
fi

HOSTNAME=$(echo "$URL" | sed 's|https://||')
echo "✅ URL détectée : $URL"

# ── Mise à jour de settings.py ────────────────────────────────────────────────
echo "🔧 Mise à jour de settings.py..."

# ALLOWED_HOSTS (sans https://)
sed -i "/ALLOWED_HOSTS/,/\]/{s|'[^']*\.trycloudflare\.com'|'$HOSTNAME'|g}" "$SETTINGS"

# CSRF_TRUSTED_ORIGINS (avec https://)
sed -i "/CSRF_TRUSTED_ORIGINS/,/\]/{s|'[^']*\.trycloudflare\.com'|'$URL'|g}" "$SETTINGS"

# SITE_PUBLIC_URL
sed -i "s|SITE_PUBLIC_URL = '.*'|SITE_PUBLIC_URL = '$URL'|g" "$SETTINGS"

echo "✅ settings.py mis à jour"

# ── Redémarrage de Gunicorn ───────────────────────────────────────────────────
echo "🔄 Redémarrage de Gunicorn..."
if systemctl is-active --quiet gunicorn-mariage.service 2>/dev/null; then
    sudo systemctl restart gunicorn-mariage.service
    echo "✅ Gunicorn redémarré"
else
    echo "⚠️  Gunicorn non trouvé via systemd (mode dev ?)"
fi

# ── Régénération du QR Code ───────────────────────────────────────────────────
echo "🔲 Génération du QR Code..."
cd "$SCRIPT_DIR"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

PROJECT_DIR="/mnt/mariage_data/BibiUnion"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"

cd "$PROJECT_DIR"

"$VENV_PYTHON" manage.py generate_qrcode
echo "✅ QR Code régénéré"

# ── Mise à jour GitHub Pages (redirection fixe) ───────────────────────────────
if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_REPO" ]; then
    echo "🌐 Mise à jour de la page de redirection GitHub Pages..."

    # Contenu HTML de redirection
    HTML_CONTENT=$(cat << HTMLEOF
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=$URL/upload/">
  <title>Mariage — Redirection</title>
  <script>window.location.replace("$URL/upload/");</script>
</head>
<body>
  <p>Redirection en cours vers le site du mariage...</p>
  <p><a href="$URL/upload/">Cliquez ici si la redirection ne fonctionne pas.</a></p>
</body>
</html>
HTMLEOF
)

    # Encode en base64
    ENCODED=$(echo -n "$HTML_CONTENT" | base64 | tr -d '\n')

    # Récupère le SHA du fichier actuel (nécessaire pour le PUT)
    SHA=$(curl -s \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$GITHUB_REPO/contents/$GITHUB_PAGES_FILE" \
        | grep '"sha"' | head -1 | sed 's/.*"sha": "\([^"]*\)".*/\1/')

    # Payload JSON
    if [ -n "$SHA" ]; then
        PAYLOAD="{\"message\":\"Update redirect to $URL\",\"content\":\"$ENCODED\",\"sha\":\"$SHA\"}"
    else
        PAYLOAD="{\"message\":\"Create redirect to $URL\",\"content\":\"$ENCODED\"}"
    fi

    # Push via l'API GitHub
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -X PUT \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        "https://api.github.com/repos/$GITHUB_REPO/contents/$GITHUB_PAGES_FILE")

    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
        echo "✅ GitHub Pages mis à jour → https://${GITHUB_REPO%/*}.github.io/${GITHUB_REPO#*/}/"
    else
        echo "⚠️  Mise à jour GitHub Pages échouée (HTTP $HTTP_STATUS) — l'URL reste accessible directement."
    fi
else
    echo "ℹ️  GitHub Pages non configuré (GITHUB_TOKEN / GITHUB_REPO non définis)."
    echo "   Pour activer la redirection fixe, exportez ces variables avant de lancer ce script."
fi

# ── Génération d'une page de redirection GitHub Pages ─────────────────────────

cat > index.html <<EOF
<!doctype html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Bienvenue sur notre site de mariage 💍</title>
    <!-- Favicon -->
    <link rel="icon" type="image/png"
        href="https://raw.githubusercontent.com/THEMEZE/BibiUnion2/main/static/img/Bridgerton_logo_square.png">

    <!-- Open Graph -->
    <meta property="og:title" content="BibiUnion — Notre Mariage">
    <meta property="og:description" content="Bienvenue sur notre site de mariage 💍">
    <meta property="og:image" content="https://raw.githubusercontent.com/THEMEZE/BibiUnion2/main/static/img/Bridgerton_logo_square.png">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://ton-domaine.fr">

    <meta http-equiv="refresh" content="0;url=${URL}/upload/">

    <script>
        window.location.replace("${URL}/upload/");
    </script>
</head>
<body>
    <p>
        Redirection...
        <a href="${URL}/upload/">
            Cliquez ici si la redirection ne fonctionne pas.
        </a>
    </p>
</body>
</html>
EOF


# ── Envoi sur GitHub ──────────────────────────────────────────────────────────

echo ""
echo "📤 Publication sur GitHub..."

echo "1. config Git" 

if ! git config --global user.name >/dev/null; then
    git config --global user.name "THEMEZE_RP"
fi

if ! git config --global user.email >/dev/null; then
    git config --global user.email "guillaume.themeze@gmail.com"
fi

echo "2. passer en SSH"

git remote set-url origin git@github.com:THEMEZE/BibiUnion2.git

echo "3. test"

ssh -T git@github.com

git add index.html

if ! git diff --cached --quiet; then
    git commit -m "Mise à jour automatique de la redirection $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
else
    echo "✔ Aucun changement à envoyer."
fi


# ── Résumé ────────────────────────────────────────────────────────────────────

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ Site en ligne !                                    ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║  Upload  : ${URL}/upload/"
echo "║  Galerie : ${URL}/gallery/"
echo "║  QR Code : ${URL}/qrcode/"
echo "║  Admin   : ${URL}/admin-gallery/"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Garde le tunnel actif
wait $TUNNEL_PID
