#!/bin/bash
set -e

# ── Couleurs ──────────────────────────────────────────────
GREEN='\033[92m'; YELLOW='\033[93m'; RED='\033[91m'; RESET='\033[0m'; BOLD='\033[1m'
ok()   { echo -e "${GREEN}  ✅  $1${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠️   $1${RESET}"; }
err()  { echo -e "${RED}  ❌  $1${RESET}"; exit 1; }

# ════════════════════════════════════════════
# 3. ENVIRONNEMENT VIRTUEL
# ════════════════════════════════════════════
echo -e "\n⏳ Création du venv..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install gunicorn -q
ok "Dépendances installées"

# ════════════════════════════════════════════
# 4. SETUP INTERACTIF (plateforme, chemins)
# ════════════════════════════════════════════
echo -e "\n⏳ Configuration de la plateforme..."
./venv/bin/python setup.py
ok "Configuration terminée"

# ════════════════════════════════════════════
# 5. BASE DE DONNÉES & FICHIERS STATIQUES
# ════════════════════════════════════════════
echo -e "\n⏳ Migrations..."
./venv/bin/python manage.py makemigrations gallery
./venv/bin/python manage.py migrate
ok "Migrations appliquées"

echo -e "\n⏳ Fichiers statiques..."
./venv/bin/python manage.py collectstatic --noinput
ok "Statiques collectés"

# ════════════════════════════════════════════
# 6. COMPTE ADMIN
# ════════════════════════════════════════════
echo -e "\n${BOLD}Création du compte administrateur :${RESET}"
./venv/bin/python manage.py createsuperuser

# ════════════════════════════════════════════
# 7. SERVICES SYSTEMD
# ════════════════════════════════════════════
echo -e "\n⏳ Installation des services systemd..."

sudo cp deploy/gunicorn-mariage.socket  /etc/systemd/system/
sudo cp deploy/gunicorn-mariage.service /etc/systemd/system/
sudo cp deploy/nginx-mariage.conf       /etc/nginx/sites-available/mariage
sudo ln -sf /etc/nginx/sites-available/mariage /etc/nginx/sites-enabled/mariage
sudo rm -f  /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-mariage.socket
sudo systemctl enable --now gunicorn-mariage.service
sudo systemctl restart nginx
ok "Services démarrés"

# ════════════════════════════════════════════
# 8. TUNNEL CLOUDFLARE
# ════════════════════════════════════════════
echo -e "\n${BOLD}╔══════════════════════════════════════════╗"
echo    "║  ✅  Installation terminée !              ║"
echo    "║  🚀  Lancement du tunnel Cloudflare...   ║"
echo -e "╚══════════════════════════════════════════╝${RESET}\n"

chmod +x start_tunnel.sh
sudo ./start_tunnel.sh

