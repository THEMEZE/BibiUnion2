# Lien fixe via GitHub Pages

Comme le tunnel Cloudflare gratuit génère une URL temporaire à chaque
démarrage, voici comment avoir un lien fixe que tu donnes aux invités
(ou imprimes sur les menus du mariage) qui redirige toujours vers le bon tunnel.

## Comment ça fonctionne

```
Invité scanne QR Code
       ↓
https://THEMEZE.github.io/mariage-redirect/
       ↓  (redirection instantanée JavaScript)
https://xyz-tunnel-du-jour.trycloudflare.com/upload/
       ↓
Site sur le Raspberry Pi
```

`start_tunnel.sh` met à jour automatiquement le fichier GitHub Pages
via l'API GitHub à chaque démarrage du tunnel.

---

## Mise en place (une seule fois)

### 1. Créer le repo GitHub Pages

1. Va sur [github.com](https://github.com) → **New repository**
2. Nom : `mariage-redirect` (ou ce que tu veux)
3. Visibilité : **Public** (obligatoire pour GitHub Pages gratuit)
4. Initialise avec un `README.md`
5. Dans **Settings → Pages** : source = branche `main`, dossier `/root`
6. Note l'URL générée : `https://TONPSEUDO.github.io/mariage-redirect/`

### 2. Créer un token GitHub

1. GitHub → **Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. **Generate new token**
3. Scope requis : `repo` (ou `contents:write` en fine-grained)
4. Copie le token (il ne s'affiche qu'une fois)

### 3. Configurer le Raspberry Pi

Ajoute ces variables dans ton environnement (ou dans `~/.bashrc`) :

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxx"
export GITHUB_REPO="TONPSEUDO/mariage-redirect"
# optionnel, par défaut index.html
export GITHUB_PAGES_FILE="index.html"
```

Ou passe-les directement au script :

```bash
GITHUB_TOKEN="ghp_xxx" GITHUB_REPO="TONPSEUDO/mariage-redirect" sudo -E ./start_tunnel.sh
```

### 4. Générer le QR Code avec le lien fixe

```bash
source venv/bin/activate
python manage.py generate_qrcode --url https://TONPSEUDO.github.io/mariage-redirect/
```

Ce QR Code ne change jamais — tu peux l'imprimer des semaines à l'avance.
Le lien GitHub Pages redirige automatiquement vers le bon tunnel au démarrage.

---

## Pourquoi ça marche sur un RPi 2B ?

La mise à jour GitHub Pages est un simple appel `curl` à l'API REST GitHub.
Aucun calcul local, aucune dépendance : ça fonctionne même sur le modèle
le plus basique du Raspberry Pi.

---

## Compatibilité

| Plateforme | Fonctionne ? |
|------------|-------------|
| RPi 2B     | ✅ |
| RPi 4      | ✅ |
| Mac        | ✅ (curl natif) |

---

## Délai de propagation GitHub Pages

La mise à jour du fichier est instantanée côté API, mais GitHub Pages
peut mettre **1 à 2 minutes** à propager le changement dans le CDN.
Lance `start_tunnel.sh` quelques minutes avant de distribuer le QR Code.
