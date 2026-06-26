#!/bin/bash
set -e

# ── Couleurs ──────────────────────────────────────────────
GREEN='\033[92m'; YELLOW='\033[93m'; RED='\033[91m'; RESET='\033[0m'; BOLD='\033[1m'
ok()   { echo -e "${GREEN}  ✅  $1${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠️   $1${RESET}"; }
err()  { echo -e "${RED}  ❌  $1${RESET}"; exit 1; }

echo -e "\n${BOLD}╔══════════════════════════════════════════╗"
echo    "║       BibiUnion — Démarrage complet      ║"
echo -e "╚══════════════════════════════════════════╝${RESET}\n"

# ════════════════════════════════════════════
# 1. CHOIX DU DÉPÔT
# ════════════════════════════════════════════
cd /mnt/mariage_data/

echo "Quel dépôt veux-tu cloner ?"
echo "  1) BibiUnion"
echo "  2) BibiUnion2"
read -p "Choix (1 ou 2) : " choice

if [ "$choice" = "1" ]; then
    REPO="https://github.com/THEMEZE/BibiUnion.git"
elif [ "$choice" = "2" ]; then
    REPO="https://github.com/THEMEZE/BibiUnion2.git"
else
    err "Choix invalide"
fi

# ════════════════════════════════════════════
# 2. CLONE
# ════════════════════════════════════════════
[ -d BibiUnion ] && sudo rm -rf BibiUnion
git clone "$REPO" BibiUnion
cd BibiUnion
ok "Clone terminé : $REPO"

#chmod +x ./run.sh
#./run.sh

