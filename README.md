Ce projet est une évolution du projet BibiUnion de [https://github.com/THEMEZE/BibiUnion].

--- 

### Cloudflare Tunnel — limite de requêtes ?

Cloudflare Tunnel (trycloudflare.com) en version gratuite n'a pas de limite stricte en nombre de requêtes, mais il y a des contraintes importantes pour ton usage :

#### Ton cas : site de mariage sur Raspberry Pi

⚠️ Le vrai goulot d'étranglement c'est le Raspberry Pi, pas Cloudflare

| **Élément** | **Limite / Réalité** |
| ---- | ---------- |
| Cloudflare Tunnel gratuit | Pas de quota de requêtes, mais pas fait pour la prod (URL temporaire qui change) |
| Upload de photos | ✅ Ça tourne bien sur RPi|
Upload de vidéos | ⚠️ Lourd — une vidéo = plusieurs centaines de Mo |
|Lecture de vidéos en streaming| ⚠️ Très limité sur RPi 3/4 selon le débit|
Vocaux| ✅ Fichiers légers, aucun problème|
|Accès simultané de plusieurs invités |⚠️ Le RPi peut saturer vite |

#### Problèmes concrets à anticiper

##### Vidéos :

- Ne pas re-encoder côté serveur (trop lent sur RPi)
- Stocker tel quel et streamer avec les headers `Range` (lecture partielle)
- Prévoir beaucoup d'espace disque (SSD externe recommandé)

##### Connexion simultanée :

- Un mariage = potentiellement 20-50 personnes qui uploadent en même temps
- Le RPi 4 (4Go RAM) peut tenir, mais augmente les timeouts gunicorn/nginx

##### Cloudflare gratuit :

- L'URL `trycloudflare.com` est temporaire et change à chaque redémarrage
- Pour une URL fixe, il faut un domaine + Cloudflare Zero Trust (gratuit jusqu'à 50 utilisateurs)

#### Recommandations pour le jour J

```
✅ RPi 4 (4Go de RAM minimum)
✅ SSD externe USB (500Go+)
✅ Nginx pour servir les fichiers statiques/médias
✅ Domaine fixe via Cloudflare Zero Trust
✅ Limiter la taille des vidéos côté frontend (ex: max 500Mo)
✅ Upload asynchrone avec barre de progression
```

Tu veux que je t'aide à structurer l'évolution pour les vidéos et vocaux ?

---

```
https://github.com/THEMEZE/BibiUnion/blob/main/README.md

J'ai fait ça pour un RPi 2B , je peut que ça soit compatible avec RPi 2B , RPI 4 , et mon Mac  (que lon puisse choissige qu debus) 

* de pourvour choisir faciment la lecalisation ( le chmin de la clef , carte sd , interne ) 
* fans le front ajouter un onglet pour afficher le Qrcode
* ajouter une option pour directement filmer , ou prendre des photo , enregistre la voe depuis le site 
* pourvoire aussi partage video et audio 
* dans la galerie cest bien le hover , je veux que pour les video , on aile meme hover maus qussi que ça joue les 5 pemier seconde de la video sans le son , et poue les audio je ne sais pas 
* Je veux que en font ça soit une image fixe absolue que je chosirais après 
* Pour le lien fixe j'ai pensait à faus en sorte que quant on le lance , ça met a jour un site githube que se redirige vers le site ( si on peut fait avec un RPI) 
* Aussi pour la DA du site je m'inpire de le serie Bridgerton
   * je veux que lon ouis slider (garde les bouton ) mais je veux que l'on puis slideer entre les mediat avec le doit sur le tels on  avec la sourie sur ordinateur 
* 
Dir moi  tous les changement  detailler
```

Voilà une belle liste d'évolutions ! Laisse-moi d'abord tout analyser et te présenter un plan détaillé avant de coder quoi que ce soit.

### Récapitulatif complet des changements demandés

#### 🖥️ Compatibilité multi-plateforme

- **RPi 2B, RPi 4, Mac** — au démarrage, on choisit la plateforme → adapte automatiquement les chemins (`/mnt/mariage_data`, `/home/pi`, `/Users/...`), le nombre de workers Gunicorn (1 pour RPi 2B, 2 pour RPi 4, auto pour Mac), et la commande cloudflared selon l'OS.

#### 📁 Choix de localisation des données

- Script interactif qui demande où stocker les médias : carte SD, disque USB monté, stockage interne — puis met à jour `MEDIA_ROOT` et les chemins dans les services systemd.

#### 📱 Onglet QR Code dans le frontend

- Nouvelle page `/qrcode/` accessible depuis la nav, qui affiche le QR Code en grand, avec un bouton "Télécharger" et l'URL en dessous.

#### 📸 Capture directe depuis le site

- Bouton "Prendre une photo" → ouvre la caméra via `getUserMedia` directement dans le navigateur, sans app tierce.
- Bouton "Filmer" → enregistrement vidéo depuis le navigateur.
- Bouton "Enregistrer un vocal" → enregistrement audio via `MediaRecorder`.

#### 🎬 Partage vidéo et audio

- Nouveau modèle `Media` (ou extension de `Photo`) pour stocker vidéos (`.mp4`, `.mov`, `.webm`) et audios (`.m4a`, `.mp3`, `.ogg`, `.webm`).
- Upload AJAX comme pour les photos, avec barre de progression.
- Limites de taille : vidéo ~500 Mo, audio ~50 Mo.
- Nginx configuré pour le streaming vidéo avec les headers `Range`.

#### 🖼️ Galerie — comportements hover améliorés

- **Photos :** hover existant conservé.
- **Vidéos :** au hover → aperçu muet des 5 premières secondes (via `<video>` avec `muted autoplay`), puis pause à la sortie. Au clic → lightbox avec lecteur complet.
- **Audio :** au hover → affichage d'une onde animée (waveform CSS) + titre. Au clic → lecteur audio inline dans la galerie.


#### 🌅 Image de fond fixe

- Fond `background-attachment: fixed` sur `body`, image configurable dans le CSS (variable `--bg-image`). Tu choisiras l'image après.

#### 🔗 Lien fixe via redirection GitHub Pages

- Un repo GitHub `mariage-redirect` avec une page `index.html` qui fait `window.location.href` vers l'URL Cloudflare du moment.
- `start_tunnel.sh` met à jour ce fichier via l'API GitHub (token en variable d'environnement), push automatiquement → GitHub Pages redirige toujours vers le bon tunnel.
- Fonctionne sur RPi 2B car c'est juste un appel `curl` à l'API GitHub.

#### 🌸 Design Bridgerton

- Palette : bleu pastel poudré (`#d4e8f0`), rose blush (`#f2d4d7`), ivoire (`#faf6f0`), or antique (`#c9a86a`), vert sauge (`#8aab96`).
- Typographie : `Playfair Display` (titres) + `Lato` (corps) via Google Fonts.
- Ornements floraux SVG en CSS (coins de cartes, séparateurs).
- Cartes avec bordure fine dorée et ombre douce.
- Boutons avec style "ruban" arrondi.

>[!tip]- ##### Palette de couleurs
>
>| Couleur | Aperçu | Code |
>|----------|---------|---------|
>| Bleu pastel poudré | <span style="display:inline-block;width:20px;height:20px;background:#d4e8f0;border:1px solid #ccc;"></span> | `#d4e8f0` |
>| Rose blush | <span style="display:inline-block;width:20px;height:20px;background:#f2d4d7;border:1px solid #ccc;"></span> | `#f2d4d7` |
>| Ivoire | <span style="display:inline-block;width:20px;height:20px;background:#faf6f0;border:1px solid #ccc;"></span> | `#faf6f0` |
>| Or antique | <span style="display:inline-block;width:20px;height:20px;background:#c9a86a;border:1px solid #ccc;"></span> | `#c9a86a` |
>| Vert sauge | <span style="display:inline-block;width:20px;height:20px;background:#8aab96;border:1px solid #ccc;"></span> | `#8aab96` |
>
>- Palette :
>  - <span style="color:#d4e8f0;">■</span> Bleu pastel poudré (`#d4e8f0`)
>  - <span style="color:#f2d4d7;">■</span> Rose blush (`#f2d4d7`)
>  - <span style="color:#faf6f0;">■</span> Ivoire (`#faf6f0`)
>  - <span style="color:#c9a86a;">■</span> Or antique (`#c9a86a`)
>  - <span style="color:#8aab96;">■</span> Vert sauge (`#8aab96`)
>
>###### Palette
>
>🔵 Bleu pastel poudré (`#d4e8f0`)
>
>🌸 Rose blush (`#f2d4d7`)
>
>🤍 Ivoire (`#faf6f0`)
>
>🟡 Or antique (`#c9a86a`)
>
>🟢 Vert sauge (`#8aab96`)

#### 👆 Swipe/Slider dans le lightbox

- Swipe tactile (touch events) sur mobile → photo/vidéo suivante ou précédente.
- Drag à la souris sur desktop → même comportement.
- Boutons précédent/suivant conservés.

#### Ce que je ne ferai PAS en une seule fois

C'est énorme — environ 800-1000 lignes de code modifiées sur 8 fichiers. Je te propose de procéder en 3 parties :

- **Partie 1** — Backend (modèles vidéo/audio, vues, URLs, settings multi-plateforme)

- **Partie 2** — Frontend HTML/CSS Bridgerton + onglet QR Code + image de fond

- **Partie 3** — JS (capture caméra/micro, upload vidéo/audio, hover vidéo, swipe, redirection GitHub)

Par quelle partie tu veux qu'on commence ?

```
Par quelle partie on commence ?

1. Partie 1 — Backend (modèles, vues, multi-plateforme)

2. Partie 2 — Design Bridgerton + QR Code + fond

3. Partie 3 — JS (caméra, swipe, hover vidéo, GitHub redirect)
```

```
Q: Par quelle partie on commence ?
A: Partie 1 — Backend (modèles, vues, multi-plateforme)
```

C'est parti pour la Partie 1 — je génère tous les fichiers backend modifiés.
Voici exactement ce qui change et pourquoi, fichier par fichier :

### Ce qui change dans la Partie 1

`gallery/models.py` — Nouveau modèle `Media` (vidéo + audio) en plus de `Photo`. Gestion des chemins d'upload, validation du type, pas de traitement Pillow pour ces formats.

`mariage/settings.py` — Nouveaux paramètres : extensions/MIME vidéo et audio autorisés, limites de taille séparées, et un `PLATFORM` détecté automatiquement.

`gallery/views.py` — Nouvelles vues : `upload_media_ajax` (vidéo/audio), `media_data` (API JSON galerie mixte), `qrcode_view` (page QR Code), mise à jour de `gallery_data` pour inclure les médias.

`gallery/urls.py` — Nouvelles routes pour les médias et le QR Code.

`gallery/migrations/` — Nouvelle migration pour le modèle `Media`.

`setup.py` — Nouveau script interactif de configuration multi-plateforme (RPi 2B / RPi 4 / Mac), choisit les chemins, workers Gunicorn, etc.

`nginx` config — Ajout des headers `Range` pour le streaming vidéo.

`requirements.txt` — Ajout de `python-magic` pour la validation MIME réelle des fichiers.

.....

Il y a un problème d'ordre de définition — `_media_upload_router` est référencé avant d'être défini. Je corrige :

......

Voici le récapitulatif détaillé de tout ce qui a été produit dans cette Partie 1 :


#### Ce qui a changé — détail fichier par fichier

##### `gallery/models.py`

Nouveau modèle `Media` ajouté à côté de `Photo` :

- Champ `media_type` (`'video'` ou `'audio'`)
- Champ `file` qui route automatiquement vers `media/videos/` ou `media/audios/` selon le type
- Champ `thumbnail` optionnel (miniature capturée côté client pour les vidéos)
- Champs `duration_seconds` et `file_size` remplis automatiquement
- `delete()` supprime les fichiers physiques comme pour `Photo`

##### `mariage/settings.py`

- Détection automatique de la plateforme via `/proc/device-tree/model` (RPi) ou `platform.system()` (Mac), surchargeble avec `MARIAGE_PLATFORM=rpi4`
- Limites séparées par type : `MAX_UPLOAD_SIZE_PHOTO` (50 Mo), `MAX_UPLOAD_SIZE_VIDEO` (300 Mo sur RPi 2B, 500 Mo ailleurs), `MAX_UPLOAD_SIZE_AUDIO`
- Extensions et **MIME** déclarés pour vidéo et audio
- `GUNICORN_WORKERS` et `GUNICORN_TIMEOUT` exportés (utilisés par `setup.py`)

##### `gallery/views.py`

- Nouvelle vue `upload_media_ajax` : reçoit vidéo ou audio, valide extension + taille, accepte la miniature canvas, enregistre le `Media`
- `gallery_data` renvoie maintenant un flux mixte photos + vidéos + audios, trié par date, avec filtre par type (`?types=photo,video`)
- Nouvelle vue `qrcode_view` → page `/qrcode/`
- Vues admin complétées : `delete_media`, `download_media`, ZIP inclut vidéos et audios dans des sous-dossiers séparés

##### `gallery/urls.py`

Nouvelles routes : `/upload/media/ajax/`, `/qrcode/`, `/admin-gallery/delete/media/<id>/`, `/admin-gallery/download/media/<id>/`

##### `gallery/migrations/0002_media.py`

Migration propre à appliquer avec `python manage.py migrate`

##### `gallery/admin.py`

Interface Django admin pour `Media` avec durée formatée et aperçu miniature/icône

##### `setup.py` (nouveau)

Script interactif qui te demande la plateforme, le chemin de stockage (SD, USB, personnalisé), le domaine, puis génère `gunicorn-mariage.service` et `nginx-mariage.conf`
 adaptés
##### `start_tunnel.sh`

Ajout de la mise à jour GitHub Pages via l'API REST : si `GITHUB_TOKEN` et `GITHUB_REPO` sont définis, il pousse un `index.html` de redirection à chaque démarrage du tunnel → lien fixe imprimable

##### `requirements.txt`
Ajout de `python-magic` pour validation MIME réelle des fichiers

---

### Ce qui change dans la Partie 2

C'est parti. Je planifie d'abord le design, puis je code.

#### Plan de design — Bridgerton

##### Palette

- #f7f0e6 — ivoire chaud (fond principal)
- #e8d5c4 — rose poudré (cartes, accents doux)
- #c9a86a — or antique (titres, bordures, CTAs)
- #6b8f7a — vert sauge (accents secondaires, nav active)
- #3d2b1f — brun nuit (texte principal)
- #f0e6d3 — crème (fond des inputs)

##### Typographie

- **Titres :** `Playfair Display` — serif élégant à empattements marqués, rappelle les feuilletons Regency
- **Corps :** `Lato` — lisible, neutre, contraste parfait avec Playfair
- **Ornements :** caractères Unicode floraux (`❧ ✦ ❦`) en Playfair comme séparateurs

**Signature unique** — Des coins ornementaux SVG dorés sur chaque carte (style cartouche Regency), et un ruban doré fin qui souligne les titres de page. Aucun autre framework ne ferait ça par défaut.

**Fond fixe** — Image configurable via variable CSS `--bg-image`, avec un voile ivoire semi-transparent par-dessus pour préserver la lisibilité.

#### Voici le récapitulatif de tout ce qui a été produit dans cette Partie 2 :

#### Ce qui a changé — détail

##### `static/css/style.css`— 1218 lignes, tout refait

**Palette Bridgerton complète —** ivoire chaud #f7f0e6, rose poudré #e8d5c4, ou antique #c9a86a, vert sauge #6b8f7a, brun nuit #3d2b1f.

**Typographie —** `Playfair Display`pour tous les titres, étiquettes de formulaire et ornements, `Lato`pour le corps. Chaque titre de page est en italique serif comme dans une gazette Regency.

**Signature Bridgerton — les pièces ornementales —** chaque `.page-card` à des pièces dorées en CSS pur via `::before` et `::after` sans aucune image. Même traitement sur le cadre QR Code.

**Fond fixe —** `.bg-fixed-layer`avec `background-attachment: fixed`(parallaxe bureau) + `.bg-veil`ivoire semi-transparent. Tu remplaces juste `--bg-image: url('')` avec ton chemin d'image. Fallback dégradé élégant si pas d'image.

**En-tête glassmorphisme —** `backdrop-filter: blur(12px)` avec bordure rose poudrée, collante, ornements `❦ ❧` encadrant le titre.

**Navigation —** pilules arrondies, état actif fond doré, icônes emoji devant chaque lien.

**Ruban doré** sous chaque titre de page ( `.title-ribbon`) — dégradé `transparent → or → transparent`, signature visuelle unique.

**Waveform audio animée —** 24 barres CSS qui pulsent en `@keyframes` quand l'enregistrement est actif.

**Hover vidéo galerie —** la `.hover-video` est positionnée `absolute` sur l'item, `opacity: 0` au repos, `opacity: 1` au hover avec transition douce.

**Toggle Diaporama —** switch iOS custom en CSS pur, sans JavaScript pour le style.

**Spinner de chargement —** cercle doré animé en CSS.

**Responsive —** grille galerie 130px → 160px → 190px selon la largeur d'écran.

**Mouvement réduit —** toutes les animations désactivées si l'utilisateur a `prefers-reduced-motion`.

##### Modèles HTML (5 fichiers)

`base.html` — deux canapés de fond ( `bg-fixed-layer` + `bg-veil`), header avec ornements, nav avec onglet QR Code, footer avec `✦ ✦ ✦`.

`upload.html` — 4 onglets (Fichiers / Photo / Vidéo / Vocal), conteneur de prévisualisation, CV post-envoi avec carte centrale.

`gallery.html` — filtres par type de média (boutons pilules), toggle Diaporama custom, lightbox avec `lightbox-media-wrap`(le JS Partie 3 et injectera image/video/audio selon le type).

`qrcode.html` — QR Code centré dans son cadre à pièces dorées, bouton téléchargement + copie du lien (JS inline personnalisé), message si QR non généré.

`admin_gallery.html` — filtres étendus avec type (photo/vidéo/audio), miniatures avec badges visuels pour vidéo et audio, actions téléchargement/suppression.

**Pour ton image de fond :** mets-la dans `static/img/`(par exemple `bg-fleurs.jpg`), puis dans style.cssla ligne 1, remplacez :

```css
--bg-image: url('');
```
par :
```css
--bg-image: url('/static/img/bg-fleurs.jpg');
```


---

### Ce qui change dans la Partie 3

C'est parti pour la partie la plus complexe — je génère tout le JavaScript en une seule fois.

Partie 3 terminée — voici le détail complet de chaque module du fichier `app.js`(804 lignes) :

#### Ce qui a changé — détail module par module

##### Module 1 — Routeur

`DOMContentLoaded` détecte quelle page est active et n'initialise que ce qui est nécessaire. Zéro code inutile chargé sur une page qui ne le concerne pas.

##### Module 2 — Téléverser des fichiers

`addFiles()` détecte automatiquement le type via le MIME ( `image/*` → photo, `video/*` → vidéo, `audio/*` → audio). L'upload photo utilise `/upload/ajax/`, les vidéos et audios utilisent `/upload/media/ajax/`avec les bons champs ( `file`, `media_type`, `duration`, `thumbnail`). La barre de progression `XHR.upload.onprogress` fonctionne pour tous les types.

##### Module 3 — Onglets
Les 4 onglets (Fichiers / Photo / Vidéo / Vocal) s'initialisent **paresseusement** — la caméra ne démarre que lorsque l'invité clique sur l'onglet pour la première fois. Éviter de demander les autorisations trop tôt.

##### Module 4 — Capture de photo

`getUserMedia({ video: true })` avec `facingMode: 'environment'` (caméra arrière par défaut sur mobile). Bouton 🔄 pour basculer caméra avant/arrière. Le snapshot est dessiné sur un `<canvas>`, converti en `File` JPEG, puis injecté dans la liste de téléchargement. Flash blanc visuel au moment du snap.

##### Module 5 — Enregistrement vidéo

`MediaRecorder` avec détection automatique du meilleur codec disponible (VP9+Opus → VP8 → WebM → MP4). Minuterie fr `00:00`. À l'arrêt, snapshot de la prévisualisation via canvas → blob envoyé comme miniature au backend. La durée est stockée dans `file._duration` et transmise au backend.

##### Module 6 — Enregistrement audio

`getUserMedia({ audio: true })` + `AudioContext` pour le visualiseur de fréquences en temps réel — les 24 barres CSS de la forme d'onde bougent vraiment en suivant le microphone via `AnalyserNode.getByteFrequencyData()`. Même logique de codec automatique.

##### Module 7 — Galerie mixte
Scrollez infiniment sur `window.scroll`, sondage temps réel toutes les 15s avec `since_id`. Les éléments photos, vidéos et audios sont rendus différemment :

- **Photo** : `<img>`classique avec lazy chargement
- **Vidéo** : `<img>`miniature + `<video class="hover-video">` en `opacity:0`, passe à `opacity:1` au hover, joue les 5 premières secondes puis s'arrête automatiquement via `setTimeout(5000)`, repart à 0 au `mouseleave`
- **Audio** : fond dégradé + icône 🎵 + 8 barres CSS de hauteurs aléatoires figées (décoratives)

##### Module 8 — Boîte lumineuse

Injectez dynamiquement `<img>`, `<video controls autoplay>`ou `<audio controls autoplay>`selon le type. La vidéo précédente est mise en pause avant de passer au suivant.

**Swipe tactile —** `touchstart`/ `touchend` sur la lightbox entière : valide si `|dx| ≥ 50px` et `|dx| > |dy|` (distingue swipe horizontal d'un scroll vertical).

**Drag souris —** `mousedown`/ `mousemove`/ `mouseup` sur `mediaWrap` : pendant le drag le média suit le curseur à 30% de sa vitesse (effet élastique), relâché au-delà de 50px → navigation, sinon retour en place avec transition.

**Animation de glissement —** à chaque navigation, le média sort vers la gauche en `opacity:0`, puis entre depuis la droite (ou inversément) avec une transition `cubic-bezier` fluide.

##### Module 9 — Diaporama
Avancez automatiquement toutes les 4,5 secondes via `setInterval`. Arrêtez proprement si on ferme la lightbox ou décoche le toggle.

##### Module 10 — Administration

Suppression différenciée : `DELETE_PHOTO_URL` pour les photos, `DELETE_MEDIA_URL` pour les vidéos/audios — les deux URL sont passées via des variables `window.*` dans le template.

---

#### Récapitulatif des 3 parties — tous les fichiers produits

| **Fichier** | **Partie** |
| ------------| -----------|
|`requirements.txt` | 1 |
|`mariage/settings.py`| 1 |
|`gallery/models.py`| 1 |
|`gallery/views.py`| 1 | 
|`gallery/urls.py` | 1 | 
|`gallery/admin.py` | 1 | 
|`gallery/migrations/0002_media.py`| 1 |
|`setup.py1start_tunnel.sh` | 1 | 
|`README_GITHUB_PAGES.md`| 1 | 
|`templates/base.html` | 2 | 
|`templates/upload.html`| 2 |
|`templates/gallery.html` | 2 | 
|`templates/qrcode.html`| 2 | 
|`templates/admin_gallery.html` | 2 | 
|`static/css/style.css` | 2 |
|`static/js/app.js`| 3 | 

---
Pour déployer, la séquence reste :

```bash
python setup.py          # choisit RPi 2B / RPi 4 / Mac interactivement
python manage.py migrate # applique la migration 0002_media
python manage.py collectstatic --noinput
sudo ./start_tunnel.sh   # lance tout
```

---


# Application Photos de Mariage

Application Django permettant aux invités de déposer leurs photos
via un QR Code, hébergée sur un Raspberry Pi 2 B et exposée publiquement
via Cloudflare Tunnel.

## Démarrage rapide

1. `./install.sh` — installe tout et configure les services
2. Configurer Cloudflare Tunnel (voir section dédiée)
3. Mettre à jour `mariage/settings.py` :
   - `ALLOWED_HOSTS`
   - `CSRF_TRUSTED_ORIGINS`
   - `SITE_PUBLIC_URL`
4. `python manage.py generate_qrcode`
5. Imprimer le QR Code (disponible dans `/admin-gallery/`) et l'afficher pendant le mariage

## Parcours invité

1. Scan du QR Code -> arrive directement sur `/upload/`
2. Saisit son nom (optionnel) et sa table (optionnel)
3. Sélectionne ou glisse ses photos
4. Envoi automatique avec barre de progression
5. Peut consulter `/gallery/` pour voir toutes les photos

## Administration

- `/admin-gallery/` : suppression, téléchargement, ZIP, QR Code
- `/admin/` : interface Django native

## Sauvegarde

Voir `backup.sh` — exécution automatique quotidienne via cron.

## Maintenance

```bash
sudo systemctl restart gunicorn-mariage nginx cloudflared
sudo journalctl -u gunicorn-mariage -f
```

> Le projet est complet et déployable. Points d'attention avant la mise en production : remplacer `SECRET_KEY`, `mondomaine.fr` et l'UUID du tunnel par vos valeurs réelles, et tester l'upload HEIC depuis un iPhone (le décodage HEIC requiert `libheif-dev` installé via `install.sh`).



# 1. Architecture du projet

```bash
mkdir -p BibiUnion/{mariage,gallery/{templates/gallery,migrations,management/commands},templates,static/{css,js},media/{photos,thumbnails,qrcodes}}
cd BibiUnion
```
Arborescence finale :

```
BibiUnion/
├── manage.py
├── requirements.txt
├── install.sh
├── README.md
├── db.sqlite3 (généré)
│
├── mariage/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── gallery/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── migrations/__init__.py
│   └── management/commands/
│       ├── __init__.py
│       └── generate_qrcode.py
│
├── templates/
│   ├── base.html
│   ├── upload.html
│   ├── gallery.html
│   └── admin_gallery.html
│
├── static/
│   ├── css/style.css
│   └── js/app.js
│
└── media/
    ├── photos/
    ├── thumbnails/
    └── qrcodes/
```

# 2. Backend Django

## `requirements.txt`

```text
Django==5.0.7
Pillow==10.4.0
gunicorn==22.0.0
qrcode==7.4.2
pillow-heif==0.18.0
python-magic==0.4.27
```

## `manage.py`

```python
#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mariage.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
```

## `mariage/__init__.py`

```python
```

## `mariage/settings.py`

```python
import os
import platform
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# DÉTECTION DE PLATEFORME
# Valeurs possibles : 'rpi2b', 'rpi4', 'mac'
# Peut être surchargé via la variable d'env MARIAGE_PLATFORM
# ============================================
def _detect_platform():
    env = os.environ.get('MARIAGE_PLATFORM', '').lower()
    if env in ('rpi2b', 'rpi4', 'mac'):
        return env
    system = platform.system()
    if system == 'Darwin':
        return 'mac'
    # Linux : essaie de lire le modèle RPi
    try:
        model = Path('/proc/device-tree/model').read_text()
        if 'Pi 4' in model or 'Pi 5' in model:
            return 'rpi4'
        return 'rpi2b'
    except Exception:
        return 'rpi2b'

PLATFORM = _detect_platform()

# ============================================
# CHEMINS PAR PLATEFORME
# ============================================
_PLATFORM_PATHS = {
    'rpi2b': {
        'project_root': Path('/mnt/mariage_data/BibiUnion'),
        'media_root':   Path('/mnt/mariage_data/BibiUnion/media'),
        'static_root':  Path('/mnt/mariage_data/BibiUnion/staticfiles'),
        'gunicorn_workers': 1,       # RPi 2B : 1 seul cœur efficace
        'gunicorn_timeout': 180,
        'upload_max_photo_mb': 50,
        'upload_max_video_mb': 300,  # limité sur RPi 2B (RAM 1 Go)
        'upload_max_audio_mb': 30,
    },
    'rpi4': {
        'project_root': Path('/mnt/mariage_data/BibiUnion'),
        'media_root':   Path('/mnt/mariage_data/BibiUnion/media'),
        'static_root':  Path('/mnt/mariage_data/BibiUnion/staticfiles'),
        'gunicorn_workers': 2,
        'gunicorn_timeout': 120,
        'upload_max_photo_mb': 50,
        'upload_max_video_mb': 500,
        'upload_max_audio_mb': 50,
    },
    'mac': {
        'project_root': BASE_DIR,
        'media_root':   BASE_DIR / 'media',
        'static_root':  BASE_DIR / 'staticfiles',
        'gunicorn_workers': 2,
        'gunicorn_timeout': 60,
        'upload_max_photo_mb': 50,
        'upload_max_video_mb': 500,
        'upload_max_audio_mb': 50,
    },
}

_cfg = _PLATFORM_PATHS[PLATFORM]

# ============================================
# SÉCURITÉ
# ============================================
SECRET_KEY = 'django-insecure-CHANGEZ-MOI-AVEC-UNE-VRAIE-CLE-SECRETE-AVANT-DEPLOIEMENT'

DEBUG = False

ALLOWED_HOSTS = [
    'photos.bibiunion.fr',
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'https://photos.bibiunion.fr',
]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================
# APPLICATIONS
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gallery',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mariage.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mariage.wsgi.application'

# ============================================
# BASE DE DONNÉES
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _cfg['project_root'] / 'db.sqlite3',
    }
}

# ============================================
# VALIDATION MOTS DE PASSE
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================
# INTERNATIONALISATION
# ============================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# ============================================
# FICHIERS STATIQUES ET MEDIA
# ============================================
STATIC_URL = 'static/'
STATIC_ROOT = _cfg['static_root']
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = _cfg['media_root']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# UPLOAD — LIMITES DE TAILLE PAR TYPE
# ============================================
_photo_mb  = _cfg['upload_max_photo_mb']
_video_mb  = _cfg['upload_max_video_mb']
_audio_mb  = _cfg['upload_max_audio_mb']
_max_mb    = max(_photo_mb, _video_mb, _audio_mb)

# Django lit le plus grand des trois pour la limite globale
FILE_UPLOAD_MAX_MEMORY_SIZE = _max_mb * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = _max_mb * 1024 * 1024

MAX_UPLOAD_SIZE_PHOTO = _photo_mb * 1024 * 1024
MAX_UPLOAD_SIZE_VIDEO = _video_mb * 1024 * 1024
MAX_UPLOAD_SIZE_AUDIO = _audio_mb * 1024 * 1024

# ← Alias pour la compatibilité avec le code existant
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_PHOTO

# ============================================
# TYPES DE FICHIERS AUTORISÉS
# ============================================
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'heic', 'webp']
ALLOWED_IMAGE_MIME_TYPES = [
    'image/jpeg', 'image/png', 'image/heic', 'image/heif', 'image/webp',
]

ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'mov', 'webm', 'avi', 'mkv']
ALLOWED_VIDEO_MIME_TYPES = [
    'video/mp4', 'video/quicktime', 'video/webm',
    'video/x-msvideo', 'video/x-matroska',
]

ALLOWED_AUDIO_EXTENSIONS = ['mp3', 'm4a', 'ogg', 'webm', 'wav', 'aac']
ALLOWED_AUDIO_MIME_TYPES = [
    'audio/mpeg', 'audio/mp4', 'audio/ogg', 'audio/webm',
    'audio/wav', 'audio/x-wav', 'audio/aac',
]

# ============================================
# PARAMÈTRES D'IMAGE
# ============================================
MAX_IMAGE_WIDTH = 1920
THUMBNAIL_WIDTH = 400

# ============================================
# PARAMÈTRES GUNICORN (exportés pour setup.py)
# ============================================
GUNICORN_WORKERS = _cfg['gunicorn_workers']
GUNICORN_TIMEOUT = _cfg['gunicorn_timeout']

# ============================================
# URL PUBLIQUE DU SITE (pour QR Code)
# ============================================
SITE_PUBLIC_URL = 'https://photos.bibiunion.fr'

# ============================================
# TABLES (plan de salle)
# ============================================
TABLE_CHOICES = [
    ('', 'Aucune table'),
    ('1', 'Table 1'),
    ('2', 'Table 2'),
    ('3', 'Table 3'),
    ('4', 'Table 4'),
    ('5', 'Table 5'),
    ('6', 'Table 6'),
    ('7', 'Table 7'),
    ('8', 'Table 8'),
    ('honneur', "Table d'honneur"),
]

LOGIN_URL = '/admin/login/'

```

## `mariage/wsgi.py`

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mariage.settings')

application = get_wsgi_application()
```

## `mariage/asgi.py`

```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mariage.settings')

application = get_asgi_application()
```

## `gallery/__init__.py`

```python
```

## `gallery/apps.py`

```python 
from django.apps import AppConfig


class GalleryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gallery'
    verbose_name = 'Galerie Mariage'
```

## `gallery/migrations/__init__.py`

```python
```

## `gallery/migrations/0002_media.py``

```python
from django.db import migrations, models
import django.db.models.deletion
import gallery.models
from django.conf import settings


class Migration(migrations.Migration):
    """
    Ajoute le modèle Media (vidéo + audio).
    À appliquer APRÈS la migration 0001_initial existante.
    """

    dependencies = [
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('media_type', models.CharField(
                    choices=[('video', 'Vidéo'), ('audio', 'Audio')],
                    max_length=10,
                    verbose_name='Type de média'
                )),
                ('file', models.FileField(
                    upload_to=gallery.models.media_upload_router,
                    verbose_name='Fichier'
                )),
                ('thumbnail', models.ImageField(
                    blank=True,
                    null=True,
                    upload_to=gallery.models.video_thumb_upload_path,
                    verbose_name='Miniature (vidéo uniquement)'
                )),
                ('date_upload', models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")),
                ('auteur', models.CharField(
                    blank=True, max_length=100, null=True, verbose_name="Nom de l'invité"
                )),
                ('table', models.CharField(
                    blank=True,
                    choices=settings.TABLE_CHOICES,
                    max_length=50,
                    null=True,
                    verbose_name='Table'
                )),
                ('duration_seconds', models.PositiveIntegerField(
                    blank=True, null=True, verbose_name='Durée (secondes)'
                )),
                ('file_size', models.PositiveBigIntegerField(
                    blank=True, null=True, verbose_name='Taille (octets)'
                )),
            ],
            options={
                'verbose_name': 'Média',
                'verbose_name_plural': 'Médias',
                'ordering': ['-date_upload'],
            },
        ),
    ]

```

## `gallery/management/__init__.py`

```python
```
## `gallery/management/commands/__init__.py`

```python
```

# 3. Modèle Django (Photo)

## `gallery/models.py`

```python
import os
import uuid
from io import BytesIO

from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ExifTags

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


# ============================================================
# CHEMINS D'UPLOAD
# ============================================================

def photo_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    return os.path.join('photos', f"{uuid.uuid4().hex}.{ext}")


def thumbnail_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    return os.path.join('thumbnails', f"{uuid.uuid4().hex}_thumb.{ext}")


def video_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    return os.path.join('videos', f"{uuid.uuid4().hex}.{ext}")


def audio_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    return os.path.join('audios', f"{uuid.uuid4().hex}.{ext}")


def video_thumb_upload_path(instance, filename):
    return os.path.join('thumbnails', f"{uuid.uuid4().hex}_vthumb.jpg")


def media_upload_router(instance, filename):
    """Choisit le sous-dossier selon le type de média."""
    if instance.media_type == 'video':
        return video_upload_path(instance, filename)
    return audio_upload_path(instance, filename)


# ============================================================
# MODÈLE PHOTO (existant, inchangé dans son comportement)
# ============================================================

class Photo(models.Model):
    """Photo déposée par un invité."""

    image     = models.ImageField(upload_to=photo_upload_path, verbose_name="Photo originale")
    thumbnail = models.ImageField(upload_to=thumbnail_upload_path, blank=True, null=True, verbose_name="Miniature")
    date_upload = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    auteur    = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom de l'invité")
    table     = models.CharField(max_length=50, blank=True, null=True, choices=settings.TABLE_CHOICES, verbose_name="Table")

    class Meta:
        ordering = ['-date_upload']
        verbose_name = "Photo"
        verbose_name_plural = "Photos"

    def __str__(self):
        nom = self.auteur or "Anonyme"
        return f"Photo de {nom} - {self.date_upload.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.image:
            self._process_image()

    def _process_image(self):
        try:
            img = Image.open(self.image.path)
            img = self._fix_orientation(img)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            max_w = settings.MAX_IMAGE_WIDTH
            if img.width > max_w:
                img = img.resize((max_w, int(img.height * max_w / img.width)), Image.LANCZOS)

            self._save_image_to_field(img, self.image, is_original=True)

            thumb = img.copy()
            tw = settings.THUMBNAIL_WIDTH
            thumb.thumbnail((tw, int(img.height * tw / img.width)), Image.LANCZOS)
            self._save_image_to_field(thumb, self.thumbnail, is_thumbnail=True)

            super().save(update_fields=['image', 'thumbnail'])
        except Exception as e:
            print(f"Erreur traitement image Photo {self.pk}: {e}")

    def _fix_orientation(self, img):
        try:
            exif = img.getexif()
            for key, val in ExifTags.TAGS.items():
                if val == 'Orientation':
                    rot = {3: 180, 6: 270, 8: 90}.get(exif.get(key))
                    if rot:
                        img = img.rotate(rot, expand=True)
                    break
        except Exception:
            pass
        return img

    def _save_image_to_field(self, pil_image, field, is_original=False, is_thumbnail=False):
        buffer = BytesIO()
        ext = os.path.splitext(self.image.name)[1].lower().lstrip('.')

        fmt_map = {'heic': 'JPEG', 'jpeg': 'JPEG', 'jpg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP'}
        save_format = fmt_map.get(ext, 'JPEG')
        out_ext     = 'jpg' if save_format == 'JPEG' else ext

        if save_format == 'JPEG' and pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')

        save_kwargs = {'format': save_format}
        if save_format == 'JPEG':
            save_kwargs.update({'quality': 85, 'optimize': True})

        pil_image.save(buffer, **save_kwargs)
        buffer.seek(0)

        if is_original:
            filename = os.path.basename(self.image.name)
            if ext == 'heic':
                old_path = self.image.path
                filename = os.path.splitext(filename)[0] + '.jpg'
                self.image.name = os.path.join('photos', filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            field.save(filename, ContentFile(buffer.read()), save=False)
        elif is_thumbnail:
            base = os.path.splitext(os.path.basename(self.image.name))[0]
            field.save(f"{base}_thumb.{out_ext}", ContentFile(buffer.read()), save=False)

    def delete(self, *args, **kwargs):
        for f in [self.image, self.thumbnail]:
            if f and os.path.isfile(f.path):
                os.remove(f.path)
        super().delete(*args, **kwargs)

    @property
    def filename(self):
        return os.path.basename(self.image.name)


# ============================================================
# MODÈLE MEDIA — vidéo et audio
# ============================================================

class Media(models.Model):
    """
    Fichier vidéo ou audio déposé par un invité.
    - Vidéos : servies via Nginx en streaming (headers Range gérés par Nginx).
    - Audios : servis directement, fichiers légers.
    - Pas de re-encodage côté serveur (trop lent sur RPi 2B).
    """

    MEDIA_TYPE_CHOICES = [
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
    ]

    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        verbose_name="Type de média"
    )

    # Fichier brut (vidéo ou audio selon media_type)
    file = models.FileField(
        upload_to=media_upload_router,
        verbose_name="Fichier"
    )

    # Miniature : générée côté client (canvas snapshot) pour les vidéos,
    # vide pour les audios (le front affiche une icône générique).
    thumbnail = models.ImageField(
        upload_to=video_thumb_upload_path,
        blank=True,
        null=True,
        verbose_name="Miniature (vidéo uniquement)"
    )

    date_upload = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    auteur = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom de l'invité")
    table  = models.CharField(
        max_length=50, blank=True, null=True,
        choices=settings.TABLE_CHOICES, verbose_name="Table"
    )

    # Durée en secondes — envoyée par le client JS avant l'upload
    duration_seconds = models.PositiveIntegerField(blank=True, null=True, verbose_name="Durée (secondes)")

    # Taille fichier en octets — calculée à la sauvegarde
    file_size = models.PositiveBigIntegerField(blank=True, null=True, verbose_name="Taille (octets)")

    class Meta:
        ordering = ['-date_upload']
        verbose_name = "Média"
        verbose_name_plural = "Médias"

    def __str__(self):
        nom = self.auteur or "Anonyme"
        return f"{self.get_media_type_display()} de {nom} - {self.date_upload.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        if self._state.adding and self.file:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        if self.thumbnail and os.path.isfile(self.thumbnail.path):
            os.remove(self.thumbnail.path)
        super().delete(*args, **kwargs)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 1) if self.file_size else None

    @property
    def is_video(self):
        return self.media_type == 'video'

    @property
    def is_audio(self):
        return self.media_type == 'audio'

```

## `gallery/forms.py`

```python 
import os
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Photo


def validate_image_extension(value):
    """Valide que l'extension du fichier est autorisée."""
    ext = os.path.splitext(value.name)[1].lower().lstrip('.')
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Format de fichier non autorisé : .{ext}. "
            f"Formats acceptés : {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
        )


def validate_image_size(value):
    """Valide que la taille du fichier ne dépasse pas la limite."""
    if value.size > settings.MAX_UPLOAD_SIZE:
        max_mo = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise ValidationError(f"Le fichier dépasse la taille maximale autorisée ({max_mo:.0f} Mo).")


class PhotoUploadForm(forms.ModelForm):
    """Formulaire d'upload d'une photo (utilisé en interne, un par fichier)."""

    image = forms.ImageField(
        validators=[validate_image_extension, validate_image_size],
        required=True,
    )

    class Meta:
        model = Photo
        fields = ['image', 'auteur', 'table']
        widgets = {
            'auteur': forms.TextInput(attrs={
                'placeholder': 'Votre nom (optionnel)',
                'class': 'input-field',
                'maxlength': '100',
            }),
            'table': forms.Select(attrs={'class': 'input-field'}),
        }

    def clean_image(self):
        """Validation supplémentaire du contenu réel de l'image."""
        image = self.cleaned_data.get('image')
        if image:
            from PIL import Image as PILImage
            try:
                img = PILImage.open(image)
                img.verify()
            except Exception:
                raise ValidationError("Le fichier envoyé n'est pas une image valide.")
            image.seek(0)
        return image
```

# 4. Base de données

## Création des migrations

```bash
python manage.py makemigrations gallery
python manage.py migrate
```

Contenu généré attendu : `gallery/migrations/0001_initial.py` (auto-généré, non modifié manuellement).



# 5. Upload (avec QR Code -> formulaire simplifié)

Le scan du QR Code amène directement sur `/upload`, où l'invité **saisit juste** son nom puis **sélectionne ses photos**.


## `gallery/views.py`

```python
import os
import zipfile
import tempfile
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.dateparse import parse_date
from django.core.files.base import ContentFile

from .models import Photo, Media
from .forms import PhotoUploadForm, validate_image_extension, validate_image_size


# ============================================================
# HELPERS
# ============================================================

def _validate_media_file(uploaded_file, media_type):
    """
    Valide extension + taille d'un fichier vidéo ou audio.
    Retourne None si OK, sinon une chaîne d'erreur.
    """
    ext = os.path.splitext(uploaded_file.name)[1].lower().lstrip('.')

    if media_type == 'video':
        allowed_ext  = settings.ALLOWED_VIDEO_EXTENSIONS
        allowed_mime = settings.ALLOWED_VIDEO_MIME_TYPES
        max_size     = settings.MAX_UPLOAD_SIZE_VIDEO
        label        = 'vidéo'
    elif media_type == 'audio':
        allowed_ext  = settings.ALLOWED_AUDIO_EXTENSIONS
        allowed_mime = settings.ALLOWED_AUDIO_MIME_TYPES
        max_size     = settings.MAX_UPLOAD_SIZE_AUDIO
        label        = 'audio'
    else:
        return "Type de média inconnu."

    if ext not in allowed_ext:
        return (
            f"Format {label} non autorisé : .{ext}. "
            f"Formats acceptés : {', '.join(allowed_ext)}"
        )

    if uploaded_file.size > max_size:
        max_mb = max_size // (1024 * 1024)
        return f"Le fichier dépasse la limite autorisée ({max_mb} Mo)."

    return None


def _photo_to_dict(photo):
    return {
        'id':            photo.id,
        'type':          'photo',
        'thumbnail_url': photo.thumbnail.url if photo.thumbnail else photo.image.url,
        'full_url':      photo.image.url,
        'auteur':        photo.auteur or 'Anonyme',
        'table':         photo.get_table_display() if photo.table else '',
        'date_upload':   photo.date_upload.strftime('%d/%m/%Y %H:%M'),
        'date_iso':      photo.date_upload.isoformat(),
    }


def _media_to_dict(media):
    return {
        'id':               media.id,
        'type':             media.media_type,          # 'video' | 'audio'
        'file_url':         media.file.url,
        'thumbnail_url':    media.thumbnail.url if media.thumbnail else None,
        'auteur':           media.auteur or 'Anonyme',
        'table':            media.get_table_display() if media.table else '',
        'date_upload':      media.date_upload.strftime('%d/%m/%Y %H:%M'),
        'date_iso':         media.date_upload.isoformat(),
        'duration_seconds': media.duration_seconds,
        'file_size_mb':     media.file_size_mb,
        'filename':         media.filename,
    }


# ============================================================
# PAGE UPLOAD
# ============================================================

def upload_view(request):
    """Page principale d'upload — photos, vidéos, audios, capture caméra/micro."""
    return render(request, 'upload.html', {
        'table_choices':    settings.TABLE_CHOICES,
        'max_photo_mo':     settings.MAX_UPLOAD_SIZE_PHOTO  // (1024 * 1024),
        'max_video_mo':     settings.MAX_UPLOAD_SIZE_VIDEO  // (1024 * 1024),
        'max_audio_mo':     settings.MAX_UPLOAD_SIZE_AUDIO  // (1024 * 1024),
        'allowed_video_ext': ','.join(f'.{e}' for e in settings.ALLOWED_VIDEO_EXTENSIONS),
        'allowed_audio_ext': ','.join(f'.{e}' for e in settings.ALLOWED_AUDIO_EXTENSIONS),
    })


# ============================================================
# UPLOAD AJAX — PHOTO
# ============================================================

@csrf_protect
@require_POST
def upload_ajax(request):
    """Upload AJAX d'une photo unique."""
    image_file = request.FILES.get('image')
    auteur     = request.POST.get('auteur', '').strip()
    table      = request.POST.get('table', '').strip()

    if not image_file:
        return JsonResponse({'success': False, 'error': "Aucun fichier reçu."}, status=400)

    try:
        validate_image_extension(image_file)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(getattr(e, 'message', e))}, status=400)

    try:
        validate_image_size(image_file)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(getattr(e, 'message', e))}, status=400)

    from PIL import Image as PILImage
    try:
        img_check = PILImage.open(image_file)
        img_check.verify()
        image_file.seek(0)
    except Exception:
        return JsonResponse({'success': False, 'error': "Fichier image invalide ou corrompu."}, status=400)

    photo = Photo(
        image=image_file,
        auteur=auteur[:100] if auteur else None,
        table=table if table else None,
    )
    photo.save()

    return JsonResponse({
        'success':       True,
        'id':            photo.id,
        'type':          'photo',
        'thumbnail_url': photo.thumbnail.url if photo.thumbnail else photo.image.url,
        'auteur':        photo.auteur or 'Anonyme',
    })


# ============================================================
# UPLOAD AJAX — VIDÉO ou AUDIO
# ============================================================

@csrf_protect
@require_POST
def upload_media_ajax(request):
    """
    Upload AJAX d'un fichier vidéo ou audio.
    Le client envoie :
      - file        : le fichier
      - media_type  : 'video' | 'audio'
      - auteur      : nom (optionnel)
      - table       : table (optionnel)
      - duration    : durée en secondes (optionnel, calculé côté client)
      - thumbnail   : image JPEG de la 1re frame (optionnel, pour vidéo)
    """
    uploaded_file = request.FILES.get('file')
    media_type    = request.POST.get('media_type', '').strip().lower()
    auteur        = request.POST.get('auteur', '').strip()
    table         = request.POST.get('table', '').strip()
    duration_raw  = request.POST.get('duration', '').strip()
    thumb_file    = request.FILES.get('thumbnail')  # optionnel, pour vidéo

    if not uploaded_file:
        return JsonResponse({'success': False, 'error': "Aucun fichier reçu."}, status=400)

    if media_type not in ('video', 'audio'):
        return JsonResponse({'success': False, 'error': "Type de média invalide (video|audio)."}, status=400)

    error = _validate_media_file(uploaded_file, media_type)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)

    # Durée
    duration = None
    if duration_raw:
        try:
            duration = int(float(duration_raw))
        except (ValueError, TypeError):
            pass

    media = Media(
        media_type=media_type,
        file=uploaded_file,
        auteur=auteur[:100] if auteur else None,
        table=table if table else None,
        duration_seconds=duration,
    )

    # Miniature vidéo envoyée par le client (canvas snapshot de la 1re frame)
    if media_type == 'video' and thumb_file:
        media.thumbnail = thumb_file

    media.save()

    return JsonResponse({
        'success':       True,
        'id':            media.id,
        'type':          media_type,
        'file_url':      media.file.url,
        'thumbnail_url': media.thumbnail.url if media.thumbnail else None,
        'auteur':        media.auteur or 'Anonyme',
        'file_size_mb':  media.file_size_mb,
    })


# ============================================================
# GALERIE PUBLIQUE
# ============================================================

def gallery_view(request):
    """Page galerie publique."""
    return render(request, 'gallery.html', {
        'table_choices': settings.TABLE_CHOICES,
    })


@require_GET
def gallery_data(request):
    """
    API JSON mixte : retourne photos + vidéos + audios mélangés,
    triés par date décroissante, avec pagination.
    Paramètres GET : page, table, date, since_id, types (photo,video,audio)
    """
    page_number  = request.GET.get('page', 1)
    table_filter = request.GET.get('table', '').strip()
    date_filter  = request.GET.get('date', '').strip()
    since_id_raw = request.GET.get('since_id', '').strip()
    # Filtre sur les types à inclure (par défaut : tout)
    types_raw    = request.GET.get('types', 'photo,video,audio')
    active_types = [t.strip() for t in types_raw.split(',') if t.strip()]

    # ---- Collecte des items ----
    items = []

    if 'photo' in active_types:
        photos = Photo.objects.all()
        if table_filter:
            photos = photos.filter(table=table_filter)
        if date_filter:
            d = parse_date(date_filter)
            if d:
                photos = photos.filter(date_upload__date=d)
        if since_id_raw:
            try:
                photos = photos.filter(id__gt=int(since_id_raw.split('_')[1] if '_' in since_id_raw else since_id_raw))
            except (ValueError, IndexError):
                pass
        for p in photos:
            d = _photo_to_dict(p)
            d['_sort_key'] = p.date_upload
            items.append(d)

    if 'video' in active_types or 'audio' in active_types:
        medias = Media.objects.all()
        type_filter_list = [t for t in active_types if t in ('video', 'audio')]
        if type_filter_list and len(type_filter_list) < 2:
            medias = medias.filter(media_type=type_filter_list[0])
        if table_filter:
            medias = medias.filter(table=table_filter)
        if date_filter:
            d = parse_date(date_filter)
            if d:
                medias = medias.filter(date_upload__date=d)
        for m in medias:
            d = _media_to_dict(m)
            d['_sort_key'] = m.date_upload
            items.append(d)

    # Mode temps réel (since_id) — retourne tout ce qu'on a trouvé
    if since_id_raw:
        for item in items:
            item.pop('_sort_key', None)
        return JsonResponse({'photos': items, 'has_next': False})

    # ---- Tri global par date décroissante ----
    items.sort(key=lambda x: x.pop('_sort_key'), reverse=True)

    # ---- Pagination ----
    page_size   = 24
    total       = len(items)
    start       = (int(page_number) - 1) * page_size
    end         = start + page_size
    page_items  = items[start:end]
    has_next    = end < total
    next_page   = int(page_number) + 1 if has_next else None

    return JsonResponse({
        'photos':      page_items,   # nom conservé pour compatibilité JS existant
        'has_next':    has_next,
        'next_page':   next_page,
        'total_count': total,
    })


# ============================================================
# PAGE QR CODE
# ============================================================

def qrcode_view(request):
    """Page affichant le QR Code en grand (accessible depuis la nav)."""
    qr_path   = os.path.join(settings.MEDIA_ROOT, 'qrcodes', 'qrcode.png')
    qr_url    = os.path.join(settings.MEDIA_URL,  'qrcodes', 'qrcode.png')
    qr_exists = os.path.isfile(qr_path)
    return render(request, 'qrcode.html', {
        'qr_url':         qr_url if qr_exists else None,
        'site_public_url': settings.SITE_PUBLIC_URL,
    })


# ============================================================
# ADMINISTRATION
# ============================================================

@staff_member_required
def admin_gallery_view(request):
    """Page d'administration : photos + médias."""
    photos = Photo.objects.all()
    medias = Media.objects.all()

    table_filter = request.GET.get('table', '').strip()
    date_filter  = request.GET.get('date',  '').strip()
    type_filter  = request.GET.get('type',  '').strip()   # 'photo'|'video'|'audio'|''

    if table_filter:
        photos = photos.filter(table=table_filter)
        medias = medias.filter(table=table_filter)
    if date_filter:
        d = parse_date(date_filter)
        if d:
            photos = photos.filter(date_upload__date=d)
            medias = medias.filter(date_upload__date=d)
    if type_filter == 'video':
        medias = medias.filter(media_type='video')
        photos = Photo.objects.none()
    elif type_filter == 'audio':
        medias = medias.filter(media_type='audio')
        photos = Photo.objects.none()
    elif type_filter == 'photo':
        medias = Media.objects.none()

    # Fusion et tri
    all_items = list(photos) + list(medias)
    all_items.sort(key=lambda x: x.date_upload, reverse=True)

    paginator  = Paginator(all_items, 48)
    page_obj   = paginator.get_page(request.GET.get('page', 1))

    qr_path   = os.path.join(settings.MEDIA_ROOT, 'qrcodes', 'qrcode.png')
    qr_url    = os.path.join(settings.MEDIA_URL,  'qrcodes', 'qrcode.png')
    qr_exists = os.path.isfile(qr_path)

    return render(request, 'admin_gallery.html', {
        'page_obj':        page_obj,
        'total_count':     paginator.count,
        'table_choices':   settings.TABLE_CHOICES,
        'qr_url':          qr_url if qr_exists else None,
        'site_public_url': settings.SITE_PUBLIC_URL,
        'selected_table':  table_filter,
        'selected_date':   date_filter,
        'selected_type':   type_filter,
    })


@staff_member_required
@require_POST
def delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    photo.delete()
    return JsonResponse({'success': True})


@staff_member_required
@require_POST
def delete_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    media.delete()
    return JsonResponse({'success': True})


@staff_member_required
def download_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    if not os.path.isfile(photo.image.path):
        raise Http404("Fichier introuvable.")
    with open(photo.image.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{photo.filename}"'
    return response


@staff_member_required
def download_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    if not os.path.isfile(media.file.path):
        raise Http404("Fichier introuvable.")
    with open(media.file.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{media.filename}"'
    return response


@staff_member_required
def download_zip(request):
    """ZIP de toutes les photos + vidéos + audios (selon filtre)."""
    photos = Photo.objects.all()
    medias = Media.objects.all()

    table_filter = request.GET.get('table', '').strip()
    date_filter  = request.GET.get('date',  '').strip()

    if table_filter:
        photos = photos.filter(table=table_filter)
        medias = medias.filter(table=table_filter)
    if date_filter:
        d = parse_date(date_filter)
        if d:
            photos = photos.filter(date_upload__date=d)
            medias = medias.filter(date_upload__date=d)

    if not photos.exists() and not medias.exists():
        raise Http404("Aucun fichier à télécharger.")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        tmp_path = tmp.name

    with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            if os.path.isfile(photo.image.path):
                arcname = f"photos/{photo.date_upload.strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
                zf.write(photo.image.path, arcname=arcname)
        for media in medias:
            if os.path.isfile(media.file.path):
                folder  = 'videos' if media.is_video else 'audios'
                arcname = f"{folder}/{media.date_upload.strftime('%Y%m%d_%H%M%S')}_{media.filename}"
                zf.write(media.file.path, arcname=arcname)

    with open(tmp_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/zip')
        zip_name = f"mariage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        response['Content-Disposition'] = f'attachment; filename="{zip_name}"'

    os.remove(tmp_path)
    return response

```

## `gallery/urls.py`

```python 
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gallery.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

```

## `gallery/admin.py`

```python 
from django.contrib import admin
from .models import Photo, Media


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display  = ('id', 'auteur', 'table', 'date_upload', 'thumbnail_preview')
    list_filter   = ('table', 'date_upload')
    search_fields = ('auteur',)
    readonly_fields = ('thumbnail_preview', 'date_upload')

    def thumbnail_preview(self, obj):
        from django.utils.html import format_html
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height:80px;" />', obj.thumbnail.url)
        return "(pas de miniature)"
    thumbnail_preview.short_description = "Aperçu"


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display  = ('id', 'media_type', 'auteur', 'table', 'date_upload', 'file_size_mb', 'duration_display', 'thumbnail_preview')
    list_filter   = ('media_type', 'table', 'date_upload')
    search_fields = ('auteur',)
    readonly_fields = ('date_upload', 'file_size', 'thumbnail_preview')

    def duration_display(self, obj):
        if obj.duration_seconds:
            m, s = divmod(obj.duration_seconds, 60)
            return f"{m}:{s:02d}"
        return "—"
    duration_display.short_description = "Durée"

    def thumbnail_preview(self, obj):
        from django.utils.html import format_html
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height:80px;" />', obj.thumbnail.url)
        icon = "🎬" if obj.is_video else "🎵"
        return icon
    thumbnail_preview.short_description = "Aperçu"

```

# 6. Frontend

## `templates/base.html`

```html 
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>{% block title %}BibiUnion — Notre Mariage{% endblock %}</title>

  <!-- Google Fonts : Playfair Display + Lato -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">

  <link rel="stylesheet" href="{% static 'css/style.css' %}">
  {% block extra_head %}{% endblock %}
</head>
<body>

  <!-- ══════════ FOND FIXE ══════════
       Remplacez l'URL dans style.css (variable --bg-image)
       par votre propre image de fond.
  ═══════════════════════════════════ -->
  <div class="bg-fixed-layer" aria-hidden="true"></div>
  <div class="bg-veil"        aria-hidden="true"></div>

  <!-- ══════════ HEADER ══════════ -->
  <header class="site-header" role="banner">
    <div class="header-inner">

      <!-- Ornement gauche -->
      <span class="header-ornament" aria-hidden="true">❦</span>

      <!-- Titre -->
      <div class="header-title-group">
        <p class="header-eyebrow">Bienvenue à</p>
        <h1 class="site-title">BibiUnion</h1>
      </div>

      <!-- Ornement droit -->
      <span class="header-ornament" aria-hidden="true">❧</span>
    </div>

    <!-- Navigation -->
    <nav class="site-nav" aria-label="Navigation principale">
      <a href="{% url 'upload' %}"  class="nav-link {% if request.resolver_match.url_name == 'upload'  %}active{% endif %}">
        <span class="nav-icon">📷</span> Partager
      </a>
      <a href="{% url 'gallery' %}" class="nav-link {% if request.resolver_match.url_name == 'gallery' %}active{% endif %}">
        <span class="nav-icon">✨</span> Galerie
      </a>
      <a href="{% url 'qrcode' %}"  class="nav-link {% if request.resolver_match.url_name == 'qrcode'  %}active{% endif %}">
        <span class="nav-icon">⬛</span> QR Code
      </a>
    </nav>
  </header>

  <!-- ══════════ CONTENU ══════════ -->
  <main class="main-content" id="main-content">
    {% block content %}{% endblock %}
  </main>

  <!-- ══════════ FOOTER ══════════ -->
  <footer class="site-footer" role="contentinfo">
    <p class="footer-ornament" aria-hidden="true">✦ ✦ ✦</p>
    <p class="footer-text">Merci de partager vos plus beaux souvenirs avec nous</p>
    <p class="footer-sub">avec amour 💛</p>
  </footer>

  <script src="{% static 'js/app.js' %}"></script>
  {% block extra_scripts %}{% endblock %}
</body>
</html>
```

## `templates/upload.html`

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Partager — BibiUnion{% endblock %}

{% block content %}
<div class="page-card upload-container">

  <!-- En-tête de page avec ruban doré -->
  <div class="page-header">
    <p class="page-eyebrow">Vos souvenirs</p>
    <h2 class="page-title">Partagez vos photos & vidéos</h2>
    <div class="title-ribbon" aria-hidden="true"></div>
    <p class="page-subtitle">
      Choisissez votre nom, votre table, puis déposez photos, vidéos ou enregistrements —
      ou capturez directement depuis votre appareil.
    </p>
  </div>

  <!-- Formulaire principal -->
  <form id="upload-form" class="upload-form" novalidate>
    {% csrf_token %}

    <!-- Nom + Table -->
    <div class="form-row">
      <div class="form-group">
        <label for="auteur" class="form-label">Votre prénom</label>
        <input type="text" id="auteur" name="auteur" class="input-field"
               placeholder="Optionnel" maxlength="100" autocomplete="given-name">
      </div>
      <div class="form-group">
        <label for="table" class="form-label">Votre table</label>
        <select id="table" name="table" class="input-field">
          {% for value, label in table_choices %}
            <option value="{{ value }}">{{ label }}</option>
          {% endfor %}
        </select>
      </div>
    </div>

    <!-- ── ONGLETS de type de partage ── -->
    <div class="upload-tabs" role="tablist" aria-label="Type de partage">
      <button type="button" class="upload-tab active" role="tab" data-tab="files"    aria-selected="true">
        📁 Fichiers
      </button>
      <button type="button" class="upload-tab"        role="tab" data-tab="camera"   aria-selected="false">
        📸 Photo
      </button>
      <button type="button" class="upload-tab"        role="tab" data-tab="video-rec" aria-selected="false">
        🎬 Vidéo
      </button>
      <button type="button" class="upload-tab"        role="tab" data-tab="audio-rec" aria-selected="false">
        🎙️ Vocal
      </button>
    </div>

    <!-- ── TAB : Fichiers ── -->
    <div class="tab-panel active" id="tab-files" role="tabpanel">
      <label class="dropzone" id="dropzone">
        <input type="file" id="file-input" name="images"
               accept="image/*,.heic,video/*,audio/*" multiple hidden>
        <div class="dropzone-content">
          <span class="dropzone-icon" aria-hidden="true">💍</span>
          <span class="dropzone-text">Touchez pour choisir vos fichiers</span>
          <span class="dropzone-subtext">
            Photos jusqu'à {{ max_photo_mo }} Mo · Vidéos jusqu'à {{ max_video_mo }} Mo · Audios jusqu'à {{ max_audio_mo }} Mo
          </span>
        </div>
      </label>
    </div>

    <!-- ── TAB : Capture photo ── -->
    <div class="tab-panel" id="tab-camera" role="tabpanel">
      <div class="capture-panel">
        <video id="camera-preview" class="capture-video" autoplay playsinline muted></video>
        <canvas id="camera-canvas" hidden></canvas>
        <div class="capture-controls">
          <button type="button" id="btn-start-camera" class="btn btn-outline">
            Activer la caméra
          </button>
          <button type="button" id="btn-snap" class="btn btn-primary" disabled>
            📸 Prendre la photo
          </button>
          <button type="button" id="btn-flip-camera" class="btn btn-ghost" disabled title="Retourner caméra">
            🔄
          </button>
        </div>
      </div>
    </div>

    <!-- ── TAB : Enregistrement vidéo ── -->
    <div class="tab-panel" id="tab-video-rec" role="tabpanel">
      <div class="capture-panel">
        <video id="video-rec-preview" class="capture-video" autoplay playsinline muted></video>
        <div class="rec-timer" id="video-rec-timer" aria-live="polite">00:00</div>
        <div class="capture-controls">
          <button type="button" id="btn-start-video" class="btn btn-outline">
            Activer la caméra
          </button>
          <button type="button" id="btn-record-video" class="btn btn-primary" disabled>
            ⏺ Démarrer
          </button>
          <button type="button" id="btn-stop-video" class="btn btn-danger" disabled>
            ⏹ Arrêter
          </button>
        </div>
      </div>
    </div>

    <!-- ── TAB : Enregistrement audio ── -->
    <div class="tab-panel" id="tab-audio-rec" role="tabpanel">
      <div class="capture-panel audio-panel">
        <div class="audio-waveform" id="audio-waveform" aria-hidden="true">
          {% for i in "123456789012345678901234" %}
            <span class="waveform-bar"></span>
          {% endfor %}
        </div>
        <div class="rec-timer" id="audio-rec-timer" aria-live="polite">00:00</div>
        <div class="capture-controls">
          <button type="button" id="btn-record-audio" class="btn btn-primary">
            🎙️ Enregistrer
          </button>
          <button type="button" id="btn-stop-audio" class="btn btn-danger" disabled>
            ⏹ Arrêter
          </button>
        </div>
      </div>
    </div>

    <!-- ── Prévisualisation des fichiers en attente ── -->
    <div id="preview-container" class="preview-container" aria-label="Aperçu des fichiers sélectionnés"></div>

    <!-- ── Bouton d'envoi ── -->
    <button type="submit" id="submit-btn" class="btn btn-primary btn-full" disabled>
      Envoyer
    </button>
  </form>

  <!-- Résumé post-envoi -->
  <div id="upload-summary" class="upload-summary" style="display:none;" aria-live="polite">
    <div class="summary-card">
      <p class="summary-icon" aria-hidden="true">💛</p>
      <p id="summary-text" class="summary-text"></p>
      <a href="{% url 'gallery' %}" class="btn btn-primary">Voir la galerie</a>
      <button type="button" class="btn btn-outline" id="add-more-btn">Ajouter d'autres souvenirs</button>
    </div>
  </div>

</div>
{% endblock %}

{% block extra_scripts %}
<script>
  window.UPLOAD_URL       = "{% url 'upload_ajax' %}";
  window.UPLOAD_MEDIA_URL = "{% url 'upload_media_ajax' %}";
  window.MAX_VIDEO_MB     = {{ max_video_mo }};
  window.MAX_AUDIO_MB     = {{ max_audio_mo }};
</script>
{% endblock %}
```

## `templates/gallery.html`

```html 
{% extends "base.html" %}
{% load static %}

{% block title %}Galerie — BibiUnion{% endblock %}

{% block content %}
<div class="page-card gallery-container">

  <div class="page-header">
    <p class="page-eyebrow">Tous vos souvenirs</p>
    <h2 class="page-title">Galerie du mariage</h2>
    <div class="title-ribbon" aria-hidden="true"></div>
  </div>

  <!-- Filtres -->
  <div class="gallery-filters" role="search" aria-label="Filtres de la galerie">

    <!-- Filtre type de média -->
    <div class="filter-type-group" role="group" aria-label="Type de média">
      <button class="filter-type-btn active" data-type="all">Tout</button>
      <button class="filter-type-btn" data-type="photo">📷 Photos</button>
      <button class="filter-type-btn" data-type="video">🎬 Vidéos</button>
      <button class="filter-type-btn" data-type="audio">🎵 Audios</button>
    </div>

    <div class="filter-fields">
      <select id="filter-table" class="input-field input-field--sm" aria-label="Filtrer par table">
        <option value="">Toutes les tables</option>
        {% for value, label in table_choices %}
          {% if value %}
            <option value="{{ value }}">{{ label }}</option>
          {% endif %}
        {% endfor %}
      </select>

      <input type="date" id="filter-date" class="input-field input-field--sm" aria-label="Filtrer par date">

      <button id="reset-filters" class="btn btn-ghost btn-sm" aria-label="Réinitialiser les filtres">
        ✕ Réinitialiser
      </button>
    </div>

    <!-- Diaporama -->
    <label class="toggle-slideshow" aria-label="Diaporama automatique">
      <input type="checkbox" id="toggle-slideshow" role="switch">
      <span class="toggle-track" aria-hidden="true"><span class="toggle-thumb"></span></span>
      <span>Diaporama</span>
    </label>
  </div>

  <!-- Grille -->
  <div id="gallery-grid" class="gallery-grid" role="list" aria-label="Galerie de médias"></div>

  <div id="gallery-loader" class="gallery-loader" aria-live="polite" style="display:none;">
    <span class="loader-spinner" aria-hidden="true"></span> Chargement…
  </div>

  <div id="gallery-empty" class="gallery-empty" aria-live="polite" style="display:none;">
    <p class="empty-ornament" aria-hidden="true">❧</p>
    <p>Aucun souvenir pour le moment.</p>
    <a href="{% url 'upload' %}" class="btn btn-outline btn-sm">Soyez le premier !</a>
  </div>
</div>

<!-- ══════════ LIGHTBOX ══════════ -->
<div id="lightbox" class="lightbox" role="dialog" aria-modal="true" aria-label="Visionneuse" style="display:none;">
  <button class="lightbox-close" id="lightbox-close" aria-label="Fermer">&times;</button>
  <button class="lightbox-prev"  id="lightbox-prev"  aria-label="Précédent">&#8249;</button>
  <button class="lightbox-next"  id="lightbox-next"  aria-label="Suivant">&#8250;</button>

  <!-- Conteneur du média actif -->
  <div class="lightbox-media-wrap" id="lightbox-media-wrap">
    <!-- rempli dynamiquement par JS selon le type : img / video / audio -->
  </div>

  <div class="lightbox-caption" id="lightbox-caption"></div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
  window.GALLERY_DATA_URL = "{% url 'gallery_data' %}";
</script>
{% endblock %}
```

## `templates/qrcode.html`

```html
{% extends "base.html" %}
{% load static %}

{% block title %}QR Code — BibiUnion{% endblock %}

{% block content %}
<div class="page-card qrcode-container">

  <div class="page-header">
    <p class="page-eyebrow">Accès rapide</p>
    <h2 class="page-title">QR Code du mariage</h2>
    <div class="title-ribbon" aria-hidden="true"></div>
    <p class="page-subtitle">
      Partagez ce code avec vos invités pour qu'ils accèdent directement à la galerie.
    </p>
  </div>

  {% if qr_url %}
    <div class="qr-frame">
      <!-- Coins ornementaux -->
      <span class="qr-corner qr-corner--tl" aria-hidden="true"></span>
      <span class="qr-corner qr-corner--tr" aria-hidden="true"></span>
      <span class="qr-corner qr-corner--bl" aria-hidden="true"></span>
      <span class="qr-corner qr-corner--br" aria-hidden="true"></span>

      <img src="{{ qr_url }}" alt="QR Code du mariage BibiUnion" class="qr-image">
    </div>

    <p class="qr-url">{{ site_public_url }}</p>

    <div class="qr-actions">
      <a href="{{ qr_url }}" download="qrcode-bibiunion.png" class="btn btn-primary">
        ⬇ Télécharger le QR Code
      </a>
      <button type="button" class="btn btn-outline" id="btn-copy-url" data-url="{{ site_public_url }}">
        📋 Copier le lien
      </button>
    </div>

    <p class="qr-hint">
      Imprimez ce QR Code et placez-le sur chaque table — vos invités peuvent scanner directement
      pour partager leurs photos et vidéos.
    </p>

  {% else %}
    <div class="qr-missing">
      <p class="empty-ornament" aria-hidden="true">❧</p>
      <p>Le QR Code n'a pas encore été généré.</p>
      <p class="qr-hint">
        Lancez la commande suivante depuis le Raspberry Pi :
      </p>
      <pre class="code-block">python manage.py generate_qrcode</pre>
    </div>
  {% endif %}

</div>
{% endblock %}

{% block extra_scripts %}
<script>
  const copyBtn = document.getElementById('btn-copy-url');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(copyBtn.dataset.url).then(() => {
        const orig = copyBtn.textContent;
        copyBtn.textContent = '✅ Lien copié !';
        setTimeout(() => copyBtn.textContent = orig, 2000);
      });
    });
  }
</script>
{% endblock %}
```

## `templates/admin_gallery.html`

```html 
{% extends "base.html" %}
{% load static %}

{% block title %}Administration — BibiUnion{% endblock %}

{% block content %}
<div class="page-card admin-container">

  <div class="page-header">
    <p class="page-eyebrow">Espace privé</p>
    <h2 class="page-title">Administration</h2>
    <div class="title-ribbon" aria-hidden="true"></div>
    <p class="admin-stats">{{ total_count }} souvenir(s) au total</p>
  </div>

  <!-- QR Code compact -->
  {% if qr_url %}
  <div class="admin-qr-row">
    <img src="{{ qr_url }}" alt="QR Code" class="admin-qr-img">
    <div>
      <p class="admin-qr-url">{{ site_public_url }}</p>
      <a href="{% url 'qrcode' %}" class="btn btn-outline btn-sm">Voir en grand</a>
    </div>
  </div>
  {% endif %}

  <!-- Filtres -->
  <div class="admin-filters">
    <form method="get" class="filter-form">
      <select name="type" class="input-field input-field--sm" aria-label="Filtrer par type">
        <option value="" {% if not selected_type %}selected{% endif %}>Tous les types</option>
        <option value="photo" {% if selected_type == 'photo' %}selected{% endif %}>📷 Photos</option>
        <option value="video" {% if selected_type == 'video' %}selected{% endif %}>🎬 Vidéos</option>
        <option value="audio" {% if selected_type == 'audio' %}selected{% endif %}>🎵 Audios</option>
      </select>
      <select name="table" class="input-field input-field--sm" aria-label="Filtrer par table">
        <option value="">Toutes les tables</option>
        {% for value, label in table_choices %}
          {% if value %}
            <option value="{{ value }}" {% if value == selected_table %}selected{% endif %}>{{ label }}</option>
          {% endif %}
        {% endfor %}
      </select>
      <input type="date" name="date" value="{{ selected_date }}" class="input-field input-field--sm" aria-label="Filtrer par date">
      <button type="submit" class="btn btn-outline btn-sm">Filtrer</button>
      <a href="{% url 'admin_gallery' %}" class="btn btn-ghost btn-sm">✕</a>
    </form>

    <a href="{% url 'download_zip' %}?table={{ selected_table }}&date={{ selected_date }}&type={{ selected_type }}"
       class="btn btn-primary btn-sm">
      ⬇ Tout télécharger (ZIP)
    </a>
  </div>

  <!-- Grille d'items -->
  <div class="admin-grid">
    {% for item in page_obj %}
      <div class="admin-card" data-id="{{ item.id }}"
           data-type="{% if item.media_type is not None %}{{ item.media_type }}{% else %}photo{% endif %}">

        <!-- Aperçu -->
        {% if item.media_type == 'video' %}
          <div class="admin-thumb admin-thumb--video">
            {% if item.thumbnail %}
              <img src="{{ item.thumbnail.url }}" alt="Miniature vidéo" loading="lazy">
            {% else %}
              <span class="admin-media-icon">🎬</span>
            {% endif %}
            <span class="media-badge">▶</span>
          </div>
        {% elif item.media_type == 'audio' %}
          <div class="admin-thumb admin-thumb--audio">
            <span class="admin-media-icon">🎵</span>
            {% if item.duration_seconds %}
              <span class="media-duration">{{ item.duration_seconds|floatformat:"0" }}s</span>
            {% endif %}
          </div>
        {% else %}
          <img src="{{ item.thumbnail.url|default:item.image.url }}"
               alt="Photo" class="admin-thumb" loading="lazy">
        {% endif %}

        <!-- Infos -->
        <div class="admin-card-info">
          <p class="admin-author">{{ item.auteur|default:"Anonyme" }}</p>
          {% if item.table %}<p class="admin-table">{{ item.get_table_display }}</p>{% endif %}
          <p class="admin-date">{{ item.date_upload|date:"d/m/Y H:i" }}</p>
        </div>

        <!-- Actions -->
        <div class="admin-actions">
          {% if item.media_type is not None %}
            <a href="{% url 'download_media' item.id %}" class="btn-icon" title="Télécharger" aria-label="Télécharger">⬇️</a>
            <button class="btn-icon delete-btn" data-id="{{ item.id }}" data-type="{{ item.media_type }}"
                    title="Supprimer" aria-label="Supprimer">🗑️</button>
          {% else %}
            <a href="{% url 'download_photo' item.id %}" class="btn-icon" title="Télécharger" aria-label="Télécharger">⬇️</a>
            <button class="btn-icon delete-btn" data-id="{{ item.id }}" data-type="photo"
                    title="Supprimer" aria-label="Supprimer">🗑️</button>
          {% endif %}
        </div>
      </div>
    {% empty %}
      <p class="admin-empty">Aucun souvenir à afficher.</p>
    {% endfor %}
  </div>

  <!-- Pagination -->
  <nav class="pagination" aria-label="Pagination">
    {% if page_obj.has_previous %}
      <a href="?page={{ page_obj.previous_page_number }}&table={{ selected_table }}&date={{ selected_date }}&type={{ selected_type }}"
         class="btn btn-outline btn-sm">← Précédent</a>
    {% endif %}
    <span class="pagination-info">Page {{ page_obj.number }} / {{ page_obj.paginator.num_pages }}</span>
    {% if page_obj.has_next %}
      <a href="?page={{ page_obj.next_page_number }}&table={{ selected_table }}&date={{ selected_date }}&type={{ selected_type }}"
         class="btn btn-outline btn-sm">Suivant →</a>
    {% endif %}
  </nav>

</div>
{% endblock %}

{% block extra_scripts %}
<script>
  window.DELETE_PHOTO_URL = "/admin-gallery/delete/photo/";
  window.DELETE_MEDIA_URL = "/admin-gallery/delete/media/";
  window.CSRF_TOKEN       = "{{ csrf_token }}";
</script>
{% endblock %}
```

## `static/css/style.css`

```css
/* ============================================================
   BIBIUNION — STYLE BRIDGERTON
   Playfair Display + Lato · Ivoire · Or antique · Rose poudré
   ============================================================ */

/* ── 1. IMPORTS & VARIABLES ─────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Lato:wght@300;400;700&display=swap');

:root {
  /* Palette Bridgerton */
  --ivory:       #f7f0e6;
  --ivory-dark:  #ede3d4;
  --cream:       #faf6f0;
  --blush:       #e8d5c4;
  --blush-dark:  #d4b89a;
  --gold:        #c9a86a;
  --gold-dark:   #a8843f;
  --gold-light:  #e8cfA0;
  --sage:        #6b8f7a;
  --sage-dark:   #4e6e5d;
  --brown:       #3d2b1f;
  --brown-light: #6b4f3a;
  --gray:        #8a7968;
  --white:       #ffffff;
  --danger:      #b85c5c;
  --success:     #6b8f7a;

  /* Typographie */
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body:    'Lato', system-ui, sans-serif;

  /* Rayons */
  --radius-sm:   6px;
  --radius:      14px;
  --radius-lg:   22px;

  /* Ombres */
  --shadow-soft:   0 4px 16px rgba(61,43,31,.08);
  --shadow-medium: 0 8px 32px rgba(61,43,31,.14);
  --shadow-gold:   0 0 0 2px var(--gold-light);

  /* Transitions */
  --ease: all .25s ease;

  /* ── FOND FIXE ─────────────────────────────────────────────
     Remplace url('') par le chemin de ton image de fond.
     Exemple : url('/static/img/bg-fleurs.jpg')
     Tu pourras aussi passer une variable Django via une balise
     <style> dans base.html si tu veux la charger dynamiquement.
  ─────────────────────────────────────────────────────────── */
  --bg-image: url('');   /* ← METS TON IMAGE ICI */
}

/* ── 2. RESET & BASE ────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body {
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.6;
  color: var(--brown);
  background-color: var(--ivory);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* ── 3. FOND FIXE ───────────────────────────────────────── */
.bg-fixed-layer {
  position: fixed;
  inset: 0;
  z-index: -2;
  background-image: var(--bg-image);
  background-size: cover;
  background-position: center;
  background-attachment: fixed;   /* parallaxe sur desktop */
}

.bg-veil {
  position: fixed;
  inset: 0;
  z-index: -1;
  /* Voile ivoire semi-transparent : préserve la lisibilité
     Augmente l'opacité (0.88 → 0.95) si l'image est trop visible */
  background: rgba(247, 240, 230, 0.88);
}

/* Sans image de fond : fallback dégradé délicat */
:root:not([style*="--bg-image: url(')"]) .bg-fixed-layer {
  background: linear-gradient(160deg, #f7f0e6 0%, #ede3d4 50%, #e8d5c4 100%);
}

/* ── 4. ORNEMENTS SVG ───────────────────────────────────── */
/* Coin ornemental Bridgerton — SVG inline via CSS clip */
.card-corner {
  position: absolute;
  width: 28px; height: 28px;
  pointer-events: none;
}
.card-corner--tl { top: 0;    left: 0;   border-top: 2px solid var(--gold); border-left: 2px solid var(--gold); border-radius: var(--radius) 0 0 0; }
.card-corner--tr { top: 0;    right: 0;  border-top: 2px solid var(--gold); border-right: 2px solid var(--gold); border-radius: 0 var(--radius) 0 0; }
.card-corner--bl { bottom: 0; left: 0;   border-bottom: 2px solid var(--gold); border-left: 2px solid var(--gold); border-radius: 0 0 0 var(--radius); }
.card-corner--br { bottom: 0; right: 0;  border-bottom: 2px solid var(--gold); border-right: 2px solid var(--gold); border-radius: 0 0 var(--radius) 0; }

/* ── 5. HEADER ──────────────────────────────────────────── */
.site-header {
  background: rgba(255,255,255,.82);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--blush-dark);
  position: sticky;
  top: 0;
  z-index: 200;
  padding: .75rem 1rem .5rem;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: .5rem;
}

.header-ornament {
  font-family: var(--font-display);
  font-size: 1.4rem;
  color: var(--gold);
  line-height: 1;
  user-select: none;
}

.header-title-group {
  text-align: center;
}

.header-eyebrow {
  font-family: var(--font-body);
  font-size: .7rem;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--gray);
  line-height: 1;
  margin-bottom: .15rem;
}

.site-title {
  font-family: var(--font-display);
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--gold-dark);
  letter-spacing: .02em;
  line-height: 1.1;
}

/* Navigation */
.site-nav {
  display: flex;
  justify-content: center;
  gap: .35rem;
  flex-wrap: wrap;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: .3rem;
  font-family: var(--font-body);
  font-size: .82rem;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--brown-light);
  text-decoration: none;
  padding: .42rem 1rem;
  border-radius: 999px;
  border: 1.5px solid transparent;
  transition: var(--ease);
}

.nav-link:hover {
  border-color: var(--gold);
  color: var(--gold-dark);
  background: rgba(201,168,106,.08);
}

.nav-link.active {
  background: var(--gold);
  color: var(--white);
  border-color: var(--gold);
}

.nav-icon { font-size: .9rem; }

/* ── 6. MAIN & PAGE-CARD ────────────────────────────────── */
.main-content {
  flex: 1;
  max-width: 860px;
  width: 100%;
  margin: 2rem auto;
  padding: 0 1rem 3rem;
}

/* Carte principale de page — signature ornementale */
.page-card {
  background: rgba(255,255,255,.78);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--blush-dark);
  border-radius: var(--radius-lg);
  padding: 2rem 1.5rem;
  position: relative;
  box-shadow: var(--shadow-soft);
}

/* Coins ornementaux sur chaque page-card (signature Bridgerton) */
.page-card::before,
.page-card::after {
  content: '';
  position: absolute;
  width: 32px; height: 32px;
  border-color: var(--gold);
  border-style: solid;
  pointer-events: none;
}

.page-card::before {
  top: 10px; left: 10px;
  border-width: 2px 0 0 2px;
  border-radius: var(--radius) 0 0 0;
}

.page-card::after {
  bottom: 10px; right: 10px;
  border-width: 0 2px 2px 0;
  border-radius: 0 0 var(--radius) 0;
}

/* Coins manquants (en-haut droite + bas gauche) via wrapper pseudo */
.page-card .page-corner-tr,
.page-card .page-corner-bl {
  position: absolute;
  width: 32px; height: 32px;
  border-color: var(--gold);
  border-style: solid;
  pointer-events: none;
}

/* ── 7. PAGE HEADER ─────────────────────────────────────── */
.page-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-eyebrow {
  font-family: var(--font-body);
  font-size: .72rem;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: var(--gray);
  margin-bottom: .3rem;
}

.page-title {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  color: var(--gold-dark);
  line-height: 1.15;
  margin-bottom: .6rem;
}

/* ── RUBAN DORÉ sous les titres (signature) ── */
.title-ribbon {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  margin: .4rem auto .8rem;
  border-radius: 1px;
}

.page-subtitle {
  font-size: .92rem;
  color: var(--brown-light);
  max-width: 480px;
  margin: 0 auto;
  line-height: 1.7;
}

/* ── 8. FORMULAIRE ──────────────────────────────────────── */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

@media (max-width: 480px) {
  .form-row { grid-template-columns: 1fr; }
}

.form-group { display: flex; flex-direction: column; gap: .3rem; }

.form-label {
  font-family: var(--font-display);
  font-size: .85rem;
  font-style: italic;
  color: var(--brown-light);
}

.input-field {
  width: 100%;
  padding: .65rem 1rem;
  background: var(--cream);
  border: 1.5px solid var(--blush-dark);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: .95rem;
  color: var(--brown);
  transition: var(--ease);
  appearance: none;
  -webkit-appearance: none;
}

.input-field:focus {
  outline: none;
  border-color: var(--gold);
  box-shadow: var(--shadow-gold);
  background: var(--white);
}

.input-field--sm { padding: .45rem .75rem; font-size: .85rem; }

select.input-field {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23c9a86a' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right .8rem center;
  padding-right: 2.2rem;
}

/* ── 9. ONGLETS UPLOAD ──────────────────────────────────── */
.upload-tabs {
  display: flex;
  gap: .4rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
  border-bottom: 1.5px solid var(--blush-dark);
  padding-bottom: .5rem;
}

.upload-tab {
  background: none;
  border: 1.5px solid transparent;
  border-radius: 999px;
  padding: .4rem .95rem;
  font-family: var(--font-body);
  font-size: .82rem;
  font-weight: 700;
  color: var(--brown-light);
  cursor: pointer;
  transition: var(--ease);
}

.upload-tab:hover  { border-color: var(--gold); color: var(--gold-dark); }
.upload-tab.active { background: var(--gold); color: var(--white); border-color: var(--gold); }

.tab-panel         { display: none; }
.tab-panel.active  { display: block; }

/* ── 10. DROPZONE ───────────────────────────────────────── */
.dropzone {
  display: block;
  border: 2px dashed var(--gold);
  border-radius: var(--radius);
  padding: 2.5rem 1rem;
  text-align: center;
  cursor: pointer;
  background: var(--ivory);
  transition: var(--ease);
  margin-bottom: 1rem;
}

.dropzone:hover,
.dropzone.dragover {
  background: var(--blush);
  border-color: var(--gold-dark);
  transform: scale(1.01);
}

.dropzone-content { display: flex; flex-direction: column; align-items: center; gap: .5rem; }
.dropzone-icon    { font-size: 2.5rem; }
.dropzone-text    { font-family: var(--font-display); font-size: 1.05rem; font-style: italic; color: var(--brown); }
.dropzone-subtext { font-size: .78rem; color: var(--gray); }

/* ── 11. CAPTURE (caméra / audio) ───────────────────────── */
.capture-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem 0;
}

.capture-video {
  width: 100%;
  max-height: 280px;
  border-radius: var(--radius);
  background: #1a1008;
  object-fit: cover;
  border: 2px solid var(--blush-dark);
}

.capture-controls {
  display: flex;
  gap: .6rem;
  flex-wrap: wrap;
  justify-content: center;
}

/* Timer d'enregistrement */
.rec-timer {
  font-family: var(--font-display);
  font-size: 1.6rem;
  color: var(--gold-dark);
  letter-spacing: .05em;
}

/* Waveform audio animée */
.audio-panel   { min-height: 180px; }

.audio-waveform {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 60px;
}

.waveform-bar {
  display: block;
  width: 4px;
  height: 8px;
  background: var(--gold);
  border-radius: 2px;
  transition: height .1s ease;
}

/* Animation quand l'enregistrement est actif */
.audio-waveform.recording .waveform-bar {
  animation: wave-pulse .6s ease-in-out infinite alternate;
}

.audio-waveform.recording .waveform-bar:nth-child(odd)  { animation-delay: .1s; }
.audio-waveform.recording .waveform-bar:nth-child(3n)   { animation-delay: .2s; }
.audio-waveform.recording .waveform-bar:nth-child(4n)   { animation-delay: .3s; }

@keyframes wave-pulse {
  from { height: 6px; }
  to   { height: 48px; }
}

/* ── 12. PRÉVISUALISATION FICHIERS ──────────────────────── */
.preview-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(86px, 1fr));
  gap: .5rem;
  margin: 1rem 0;
}

.preview-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--blush);
  border: 1.5px solid var(--blush-dark);
}

.preview-item img,
.preview-item video {
  width: 100%; height: 100%;
  object-fit: cover;
}

.preview-item--audio {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  background: var(--ivory-dark);
}

.preview-item--video .media-type-badge {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: rgba(61,43,31,.35);
  color: white;
}

.preview-progress {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
  background: rgba(255,255,255,.4);
}

.preview-progress-bar {
  height: 100%;
  background: var(--gold);
  width: 0;
  transition: width .15s ease;
}

.preview-status {
  position: absolute;
  top: 3px; right: 3px;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: rgba(255,255,255,.9);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: .75rem;
}

.preview-status.success { color: var(--success); }
.preview-status.error   { color: var(--danger);  }

.preview-remove {
  position: absolute;
  top: 3px; left: 3px;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: rgba(61,43,31,.55);
  color: white;
  border: none;
  cursor: pointer;
  font-size: .8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--ease);
}

.preview-remove:hover { background: rgba(61,43,31,.85); }

/* ── 13. BOUTONS ────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: .4rem;
  font-family: var(--font-body);
  font-weight: 700;
  font-size: .9rem;
  letter-spacing: .04em;
  text-transform: uppercase;
  text-decoration: none;
  padding: .7rem 1.6rem;
  border-radius: 999px;
  border: 1.5px solid transparent;
  cursor: pointer;
  transition: var(--ease);
  white-space: nowrap;
}

.btn-full { width: 100%; }

.btn-primary {
  background: var(--gold);
  color: var(--white);
  border-color: var(--gold);
}
.btn-primary:hover:not(:disabled) {
  background: var(--gold-dark);
  border-color: var(--gold-dark);
  box-shadow: 0 4px 14px rgba(168,132,63,.35);
}

.btn-outline {
  background: transparent;
  color: var(--gold-dark);
  border-color: var(--gold);
}
.btn-outline:hover:not(:disabled) {
  background: rgba(201,168,106,.1);
}

.btn-ghost {
  background: transparent;
  color: var(--brown-light);
  border-color: var(--blush-dark);
}
.btn-ghost:hover { background: var(--blush); }

.btn-danger {
  background: var(--danger);
  color: var(--white);
  border-color: var(--danger);
}
.btn-danger:hover { filter: brightness(.9); }

.btn-sm { padding: .42rem 1rem; font-size: .78rem; }

.btn:disabled {
  background: var(--blush-dark);
  color: var(--gray);
  border-color: var(--blush-dark);
  cursor: not-allowed;
  box-shadow: none;
}

/* ── 14. RÉSUMÉ POST-UPLOAD ─────────────────────────────── */
.upload-summary { margin-top: 2rem; }

.summary-card {
  text-align: center;
  background: var(--ivory);
  border: 1.5px solid var(--gold-light);
  border-radius: var(--radius);
  padding: 2rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.summary-icon { font-size: 2.5rem; }
.summary-text { font-family: var(--font-display); font-size: 1.1rem; font-style: italic; color: var(--brown); }

/* ── 15. GALERIE ─────────────────────────────────────────── */
.gallery-filters {
  display: flex;
  flex-direction: column;
  gap: .75rem;
  margin-bottom: 1.5rem;
}

.filter-type-group {
  display: flex;
  gap: .35rem;
  flex-wrap: wrap;
}

.filter-type-btn {
  background: none;
  border: 1.5px solid var(--blush-dark);
  border-radius: 999px;
  padding: .38rem .9rem;
  font-family: var(--font-body);
  font-size: .8rem;
  font-weight: 700;
  color: var(--brown-light);
  cursor: pointer;
  transition: var(--ease);
}
.filter-type-btn:hover  { border-color: var(--gold); color: var(--gold-dark); }
.filter-type-btn.active { background: var(--gold); color: var(--white); border-color: var(--gold); }

.filter-fields {
  display: flex;
  gap: .5rem;
  flex-wrap: wrap;
  align-items: center;
}

.filter-fields .input-field { flex: 1; min-width: 110px; }

/* Toggle Diaporama */
.toggle-slideshow {
  display: inline-flex;
  align-items: center;
  gap: .55rem;
  font-size: .85rem;
  color: var(--brown-light);
  cursor: pointer;
  user-select: none;
}

.toggle-slideshow input { display: none; }

.toggle-track {
  width: 38px; height: 22px;
  background: var(--blush-dark);
  border-radius: 999px;
  position: relative;
  transition: background .2s;
  flex-shrink: 0;
}

.toggle-thumb {
  position: absolute;
  top: 3px; left: 3px;
  width: 16px; height: 16px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 1px 4px rgba(0,0,0,.2);
  transition: transform .2s;
}

.toggle-slideshow input:checked ~ .toggle-track { background: var(--gold); }
.toggle-slideshow input:checked ~ .toggle-track .toggle-thumb { transform: translateX(16px); }

/* Grille galerie */
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: .6rem;
}

/* Item galerie */
.gallery-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: pointer;
  background: var(--blush);
  box-shadow: var(--shadow-soft);
  transition: transform .22s ease, box-shadow .22s ease;
}

.gallery-item:hover {
  transform: scale(1.03);
  box-shadow: var(--shadow-medium);
}

/* Image */
.gallery-item img {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
  transition: opacity .2s;
}

/* Vidéo hover (5 premières secondes, muet) */
.gallery-item .hover-video {
  position: absolute;
  inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity .3s;
  pointer-events: none;
}

.gallery-item:hover .hover-video { opacity: 1; }
.gallery-item:hover .gallery-thumb-img { opacity: 0; }

/* Badge type */
.gallery-type-badge {
  position: absolute;
  top: 5px; left: 5px;
  background: rgba(61,43,31,.65);
  color: white;
  font-size: .75rem;
  padding: 2px 6px;
  border-radius: 4px;
  backdrop-filter: blur(4px);
}

/* Audio : fond spécial */
.gallery-item--audio {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--ivory-dark), var(--blush));
}

.gallery-item--audio .audio-gallery-icon {
  font-size: 2rem;
  margin-bottom: .3rem;
}

.gallery-item--audio .audio-gallery-bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 24px;
}

.gallery-item--audio .audio-gallery-bars span {
  display: block;
  width: 3px;
  background: var(--gold);
  border-radius: 2px;
  opacity: .6;
}

/* Légende au hover */
.gallery-item-caption {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(61,43,31,.75));
  color: white;
  font-size: .7rem;
  padding: .3rem .4rem;
  opacity: 0;
  transition: opacity .2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gallery-item:hover .gallery-item-caption { opacity: 1; }

/* États galerie */
.gallery-loader {
  text-align: center;
  padding: 2rem;
  color: var(--gray);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .6rem;
}

.loader-spinner {
  display: inline-block;
  width: 20px; height: 20px;
  border: 2px solid var(--blush-dark);
  border-top-color: var(--gold);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.gallery-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--gray);
}

.empty-ornament {
  font-family: var(--font-display);
  font-size: 2.5rem;
  color: var(--gold-light);
  display: block;
  margin-bottom: .5rem;
}

/* ── 16. LIGHTBOX ───────────────────────────────────────── */
.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(28,18,10,.93);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
  /* Swipe via JS — overflow caché */
  overflow: hidden;
}

.lightbox-media-wrap {
  position: relative;
  max-width: 92vw;
  max-height: 82vh;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Transition swipe */
  transition: transform .28s cubic-bezier(.25,.46,.45,.94), opacity .2s;
}

.lightbox-media-wrap img,
.lightbox-media-wrap video {
  max-width: 100%;
  max-height: 82vh;
  object-fit: contain;
  border-radius: var(--radius-sm);
  display: block;
}

.lightbox-media-wrap audio {
  width: min(400px, 90vw);
}

.lightbox-audio-wrapper {
  text-align: center;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.lightbox-audio-icon { font-size: 4rem; }

.lightbox-close,
.lightbox-prev,
.lightbox-next {
  position: absolute;
  background: rgba(255,255,255,.12);
  border: none;
  color: white;
  font-size: 1.8rem;
  cursor: pointer;
  padding: .5rem .9rem;
  border-radius: var(--radius-sm);
  transition: background .18s;
  z-index: 10;
}

.lightbox-close:hover,
.lightbox-prev:hover,
.lightbox-next:hover { background: rgba(255,255,255,.28); }

.lightbox-close { top: 1rem; right: 1rem; }
.lightbox-prev  { left: .75rem;  top: 50%; transform: translateY(-50%); }
.lightbox-next  { right: .75rem; top: 50%; transform: translateY(-50%); }

.lightbox-caption {
  position: absolute;
  bottom: 1.25rem;
  color: rgba(255,255,255,.85);
  font-size: .85rem;
  background: rgba(0,0,0,.4);
  padding: .35rem 1rem;
  border-radius: 999px;
  backdrop-filter: blur(4px);
  max-width: 80%;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── 17. PAGE QR CODE ────────────────────────────────────── */
.qrcode-container { max-width: 460px; margin: 0 auto; text-align: center; }

/* Cadre ornemental autour du QR */
.qr-frame {
  position: relative;
  display: inline-block;
  padding: 1.25rem;
  margin: 1.5rem 0 1rem;
  background: white;
  border-radius: var(--radius);
  box-shadow: var(--shadow-medium);
}

/* Coins dorés du cadre QR — signature Bridgerton */
.qr-corner {
  position: absolute;
  width: 22px; height: 22px;
  border-color: var(--gold);
  border-style: solid;
  pointer-events: none;
}

.qr-corner--tl { top: 6px;    left: 6px;   border-width: 2px 0 0 2px;  border-radius: 4px 0 0 0; }
.qr-corner--tr { top: 6px;    right: 6px;  border-width: 2px 2px 0 0;  border-radius: 0 4px 0 0; }
.qr-corner--bl { bottom: 6px; left: 6px;   border-width: 0 0 2px 2px;  border-radius: 0 0 0 4px; }
.qr-corner--br { bottom: 6px; right: 6px;  border-width: 0 2px 2px 0;  border-radius: 0 0 4px 0; }

.qr-image {
  display: block;
  width: min(220px, 70vw);
  height: auto;
}

.qr-url {
  font-family: var(--font-body);
  font-size: .8rem;
  color: var(--gray);
  word-break: break-all;
  margin-bottom: 1.25rem;
}

.qr-actions {
  display: flex;
  gap: .6rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.qr-hint {
  font-size: .85rem;
  color: var(--brown-light);
  font-style: italic;
  line-height: 1.7;
}

.qr-missing { padding: 2rem 0; }

.code-block {
  display: inline-block;
  background: var(--brown);
  color: var(--gold-light);
  font-size: .82rem;
  padding: .6rem 1.2rem;
  border-radius: var(--radius-sm);
  font-family: 'Courier New', monospace;
  margin-top: .75rem;
  word-break: break-all;
}

/* ── 18. ADMINISTRATION ─────────────────────────────────── */
.admin-container { max-width: 1000px; }

.admin-stats {
  text-align: center;
  color: var(--gray);
  font-size: .85rem;
  margin-top: -.5rem;
  margin-bottom: 1rem;
}

.admin-qr-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--ivory);
  border: 1px solid var(--blush-dark);
  border-radius: var(--radius);
  padding: .75rem 1rem;
  margin-bottom: 1.25rem;
}

.admin-qr-img { width: 64px; height: 64px; border-radius: 6px; }
.admin-qr-url { font-size: .78rem; color: var(--gray); word-break: break-all; margin-bottom: .4rem; }

.admin-filters {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: .75rem;
  margin-bottom: 1.5rem;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: .4rem;
  align-items: center;
}

/* Admin grid */
.admin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(136px, 1fr));
  gap: .65rem;
  margin-bottom: 1.5rem;
}

.admin-card {
  background: var(--ivory);
  border: 1px solid var(--blush-dark);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-soft);
  transition: var(--ease);
}

.admin-card:hover { box-shadow: var(--shadow-medium); }

.admin-thumb {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  display: block;
}

.admin-thumb--video,
.admin-thumb--audio {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background: var(--ivory-dark);
  font-size: 2rem;
  gap: .3rem;
  position: relative;
}

.admin-thumb--video img { width: 100%; height: 100%; object-fit: cover; position: absolute; inset: 0; }

.admin-media-icon { font-size: 2rem; }

.media-badge {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: rgba(61,43,31,.35);
  color: white;
  opacity: 0;
  transition: opacity .2s;
}

.admin-thumb--video:hover .media-badge { opacity: 1; }

.media-duration {
  font-size: .7rem;
  color: var(--gray);
  margin-top: .25rem;
}

.admin-card-info {
  padding: .4rem .6rem;
  font-size: .74rem;
}

.admin-author { font-weight: 700; color: var(--brown); margin-bottom: .1rem; }
.admin-table,
.admin-date   { color: var(--gray); line-height: 1.4; }

.admin-actions {
  display: flex;
  justify-content: space-around;
  padding: .35rem .25rem;
  border-top: 1px solid var(--blush-dark);
}

.btn-icon {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  text-decoration: none;
  padding: .25rem .45rem;
  border-radius: 6px;
  transition: background .15s;
}

.btn-icon:hover { background: var(--blush); }

.admin-empty {
  grid-column: 1 / -1;
  text-align: center;
  color: var(--gray);
  padding: 2rem;
  font-style: italic;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--blush-dark);
}

.pagination-info {
  font-size: .85rem;
  color: var(--gray);
  font-family: var(--font-display);
  font-style: italic;
}

/* ── 19. FOOTER ─────────────────────────────────────────── */
.site-footer {
  text-align: center;
  padding: 2rem 1rem 2.5rem;
  color: var(--gray);
}

.footer-ornament {
  font-family: var(--font-display);
  color: var(--gold-light);
  letter-spacing: .5rem;
  font-size: 1rem;
  margin-bottom: .4rem;
}

.footer-text {
  font-family: var(--font-display);
  font-style: italic;
  font-size: .9rem;
  color: var(--brown-light);
  margin-bottom: .2rem;
}

.footer-sub { font-size: .78rem; }

/* ── 20. RESPONSIVE ─────────────────────────────────────── */
@media (min-width: 540px) {
  .gallery-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
  .gallery-filters { flex-direction: row; flex-wrap: wrap; align-items: center; }
}

@media (min-width: 768px) {
  .site-title  { font-size: 2rem; }
  .page-title  { font-size: 2.4rem; }
  .page-card   { padding: 2.5rem 2.5rem; }
  .gallery-grid { grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); }
  .admin-grid  { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
}

/* ── 21. ACCESSIBILITÉ & REDUCED MOTION ─────────────────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
  .bg-fixed-layer { background-attachment: scroll; }
}

:focus-visible {
  outline: 2px solid var(--gold);
  outline-offset: 3px;
  border-radius: 4px;
}

```

## `static/js/app.js`

```js 
/* ============================================================
   BIBIUNION — app.js  (Partie 3)
   Modules :
     1.  Router principal
     2.  Upload — fichiers (photo / vidéo / audio)
     3.  Onglets upload
     4.  Capture photo (caméra)
     5.  Enregistrement vidéo
     6.  Enregistrement audio
     7.  Galerie mixte + scroll infini + temps réel
     8.  Lightbox (image / vidéo / audio) + swipe tactile + drag souris
     9.  Diaporama automatique
     10. Administration
   ============================================================ */

'use strict';

const SWIPE_THRESHOLD   = 50;    // px minimum pour valider un swipe/drag
const REALTIME_INTERVAL = 15000; // ms entre chaque poll temps réel

/* ── 1. ROUTER ────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('upload-form'))     initUploadPage();
  if (document.getElementById('gallery-grid'))    initGalleryPage();
  if (document.querySelector('.admin-container')) initAdminPage();
});


/* ══════════════════════════════════════════════════════════
   2. PAGE UPLOAD
   ══════════════════════════════════════════════════════════ */

function initUploadPage() {
  const form             = document.getElementById('upload-form');
  const dropzone         = document.getElementById('dropzone');
  const fileInput        = document.getElementById('file-input');
  const previewContainer = document.getElementById('preview-container');
  const submitBtn        = document.getElementById('submit-btn');
  const summary          = document.getElementById('upload-summary');
  const summaryText      = document.getElementById('summary-text');
  const addMoreBtn       = document.getElementById('add-more-btn');

  let selectedFiles = [];

  initUploadTabs();

  /* Drag & drop */
  ['dragenter', 'dragover'].forEach(ev =>
    dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.add('dragover'); })
  );
  ['dragleave', 'drop'].forEach(ev =>
    dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.remove('dragover'); })
  );
  dropzone.addEventListener('drop', e => addFiles(Array.from(e.dataTransfer.files)));
  fileInput.addEventListener('change', () => { addFiles(Array.from(fileInput.files)); fileInput.value = ''; });

  /* Appelé depuis les modules de capture */
  window._addCapturedFile = (file, type) => addFiles([file], type);

  function detectType(file) {
    if (file.type.startsWith('image/') || /\.heic$/i.test(file.name)) return 'photo';
    if (file.type.startsWith('video/')) return 'video';
    if (file.type.startsWith('audio/')) return 'audio';
    return 'photo';
  }

  function addFiles(files, forceType = null) {
    files.forEach(file => {
      const type = forceType || detectType(file);
      const id   = 'f_' + Math.random().toString(36).slice(2, 9);
      const entry = { id, file, type, status: 'pending', thumbnail: null, duration: file._duration || null };
      selectedFiles.push(entry);
      renderPreview(entry);
    });
    updateSubmitBtn();
  }

  function renderPreview(entry) {
    const { id, file, type } = entry;
    const item = document.createElement('div');
    item.className  = 'preview-item';
    item.dataset.id = id;

    if (type === 'photo') {
      const img = document.createElement('img');
      img.alt = 'Aperçu';
      if (!file.name.toLowerCase().endsWith('.heic')) {
        const reader = new FileReader();
        reader.onload = e => { img.src = e.target.result; };
        reader.readAsDataURL(file);
      } else {
        item.textContent = '📷';
        item.style.cssText = 'display:flex;align-items:center;justify-content:center;font-size:2rem;';
      }
      item.appendChild(img);

    } else if (type === 'video') {
      item.classList.add('preview-item--video');
      const badge = document.createElement('div');
      badge.className = 'media-type-badge';
      badge.textContent = '🎬';
      item.appendChild(badge);

      /* Snapshot de la 1re frame via canvas */
      snapVideoThumbnail(file).then(result => {
        if (!result) return;
        const img = document.createElement('img');
        img.src = result.dataUrl;
        img.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;';
        item.insertBefore(img, badge);
        entry.thumbnail = result.blob;
      });

    } else {
      item.classList.add('preview-item--audio');
      item.textContent = '🎵';
      item.style.cssText = 'display:flex;align-items:center;justify-content:center;font-size:2rem;';
    }

    /* Bouton supprimer */
    const rm = document.createElement('button');
    rm.type = 'button'; rm.className = 'preview-remove'; rm.innerHTML = '&times;';
    rm.setAttribute('aria-label', 'Retirer ce fichier');
    rm.addEventListener('click', () => {
      selectedFiles = selectedFiles.filter(f => f.id !== id);
      item.remove();
      updateSubmitBtn();
    });
    item.appendChild(rm);

    /* Barre de progression */
    const pw = document.createElement('div'); pw.className = 'preview-progress';
    const pb = document.createElement('div'); pb.className = 'preview-progress-bar';
    pw.appendChild(pb); item.appendChild(pw);

    previewContainer.appendChild(item);
  }

  function updateSubmitBtn() {
    const pending = selectedFiles.filter(f => f.status === 'pending' || f.status === 'error');
    submitBtn.disabled    = pending.length === 0;
    submitBtn.textContent = pending.length
      ? `Envoyer ${pending.length} souvenir${pending.length > 1 ? 's' : ''}`
      : 'Envoyer';
  }

  /* Soumission */
  form.addEventListener('submit', e => {
    e.preventDefault();
    const auteur    = document.getElementById('auteur').value.trim();
    const table     = document.getElementById('table').value;
    const csrf      = form.querySelector('[name=csrfmiddlewaretoken]').value;
    const toUpload  = selectedFiles.filter(f => f.status === 'pending' || f.status === 'error');
    if (!toUpload.length) return;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Envoi en cours…';

    let done = 0, ok = 0;
    toUpload.forEach(entry => {
      uploadOne(entry, auteur, table, csrf, () => {
        done++;
        if (entry.status === 'success') ok++;
        if (done === toUpload.length) onAllDone(ok, toUpload.length);
      });
    });
  });

  function uploadOne(entry, auteur, table, csrf, cb) {
    const item = previewContainer.querySelector(`[data-id="${entry.id}"]`);
    const pb   = item?.querySelector('.preview-progress-bar');
    const fd   = new FormData();
    fd.append('auteur', auteur);
    fd.append('table', table);

    let url;
    if (entry.type === 'photo') {
      fd.append('image', entry.file);
      url = window.UPLOAD_URL;
    } else {
      fd.append('file', entry.file);
      fd.append('media_type', entry.type);
      if (entry.duration) fd.append('duration', String(Math.round(entry.duration)));
      if (entry.thumbnail) fd.append('thumbnail', entry.thumbnail, 'thumb.jpg');
      url = window.UPLOAD_MEDIA_URL;
    }

    const xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('X-CSRFToken', csrf);

    xhr.upload.onprogress = e => {
      if (e.lengthComputable && pb) pb.style.width = (e.loaded / e.total * 100) + '%';
    };

    xhr.onload = () => {
      try {
        const res = JSON.parse(xhr.responseText);
        if (xhr.status === 200 && res.success) {
          entry.status = 'success'; markStatus(item, 'success', '✓');
        } else {
          entry.status = 'error'; markStatus(item, 'error', '✗', res.error);
        }
      } catch { entry.status = 'error'; markStatus(item, 'error', '✗', 'Réponse invalide'); }
      cb();
    };
    xhr.onerror = () => { entry.status = 'error'; markStatus(item, 'error', '✗', 'Erreur réseau'); cb(); };
    xhr.send(fd);
  }

  function markStatus(item, cls, icon, msg) {
    if (!item) return;
    const el = document.createElement('div');
    el.className = `preview-status ${cls}`; el.textContent = icon;
    if (msg) el.title = msg;
    item.appendChild(el);
  }

  function onAllDone(ok, total) {
    form.style.display    = 'none';
    summary.style.display = 'block';
    summaryText.textContent = ok === total
      ? `${ok} souvenir${ok > 1 ? 's' : ''} envoyé${ok > 1 ? 's' : ''} avec succès 💛`
      : `${ok}/${total} réussi${ok > 1 ? 's' : ''} — relancez pour les erreurs.`;
  }

  addMoreBtn?.addEventListener('click', () => {
    selectedFiles = [];
    previewContainer.innerHTML = '';
    form.style.display    = 'block';
    summary.style.display = 'none';
    submitBtn.disabled    = true;
    submitBtn.textContent = 'Envoyer';
  });
}

/* ── Helper snapshot vidéo ── */
function snapVideoThumbnail(file) {
  return new Promise(resolve => {
    const url   = URL.createObjectURL(file);
    const video = document.createElement('video');
    video.muted = true; video.preload = 'metadata'; video.src = url;
    video.addEventListener('loadeddata', () => { video.currentTime = 0.5; });
    video.addEventListener('seeked', () => {
      const c = document.createElement('canvas');
      c.width  = 320;
      c.height = video.videoHeight ? Math.round(video.videoHeight / video.videoWidth * 320) : 180;
      c.getContext('2d').drawImage(video, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      c.toBlob(blob => resolve({ dataUrl: c.toDataURL('image/jpeg', .8), blob }), 'image/jpeg', .8);
    }, { once: true });
    video.addEventListener('error', () => { URL.revokeObjectURL(url); resolve(null); });
  });
}


/* ══════════════════════════════════════════════════════════
   3. ONGLETS UPLOAD
   ══════════════════════════════════════════════════════════ */

function initUploadTabs() {
  const tabs   = document.querySelectorAll('.upload-tab');
  const panels = document.querySelectorAll('.tab-panel');

  tabs.forEach(tab => tab.addEventListener('click', () => {
    tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
    panels.forEach(p => p.classList.remove('active'));
    tab.classList.add('active'); tab.setAttribute('aria-selected', 'true');

    const panel = document.getElementById('tab-' + tab.dataset.tab);
    panel?.classList.add('active');

    if (tab.dataset.tab === 'camera'    && !tab._init) { initCameraCapture();  tab._init = true; }
    if (tab.dataset.tab === 'video-rec' && !tab._init) { initVideoCapture();   tab._init = true; }
    if (tab.dataset.tab === 'audio-rec' && !tab._init) { initAudioCapture();   tab._init = true; }
  }));
}


/* ══════════════════════════════════════════════════════════
   4. CAPTURE PHOTO (caméra)
   ══════════════════════════════════════════════════════════ */

function initCameraCapture() {
  const preview  = document.getElementById('camera-preview');
  const canvas   = document.getElementById('camera-canvas');
  const btnStart = document.getElementById('btn-start-camera');
  const btnSnap  = document.getElementById('btn-snap');
  const btnFlip  = document.getElementById('btn-flip-camera');
  if (!preview) return;

  let stream = null, facing = 'environment';

  async function startCam() {
    try {
      stream?.getTracks().forEach(t => t.stop());
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facing, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false,
      });
      preview.srcObject = stream;
      btnSnap.disabled  = false; btnFlip.disabled = false;
      btnStart.textContent = 'Recadrer';
    } catch (err) { alert(`Caméra inaccessible : ${err.message}`); }
  }

  btnStart.addEventListener('click', startCam);
  btnFlip.addEventListener('click',  () => { facing = facing === 'environment' ? 'user' : 'environment'; startCam(); });

  btnSnap.addEventListener('click', () => {
    if (!stream) return;
    const w = preview.videoWidth || 1280, h = preview.videoHeight || 720;
    canvas.width = w; canvas.height = h;
    canvas.getContext('2d').drawImage(preview, 0, 0, w, h);
    canvas.toBlob(blob => {
      const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
      window._addCapturedFile(file, 'photo');
      preview.style.filter = 'brightness(2)';
      setTimeout(() => preview.style.filter = '', 120);
    }, 'image/jpeg', 0.9);
  });
}


/* ══════════════════════════════════════════════════════════
   5. ENREGISTREMENT VIDÉO
   ══════════════════════════════════════════════════════════ */

function initVideoCapture() {
  const preview   = document.getElementById('video-rec-preview');
  const timerEl   = document.getElementById('video-rec-timer');
  const btnStart  = document.getElementById('btn-start-video');
  const btnRecord = document.getElementById('btn-record-video');
  const btnStop   = document.getElementById('btn-stop-video');
  if (!preview) return;

  let stream = null, recorder = null, chunks = [], elapsed = 0, timerInt = null;

  btnStart.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      preview.srcObject = stream;
      btnRecord.disabled = false;
      btnStart.textContent = 'Caméra active';
    } catch (err) { alert(`Caméra inaccessible : ${err.message}`); }
  });

  btnRecord.addEventListener('click', () => {
    if (!stream) return;
    chunks = []; elapsed = 0;
    const mime = bestMime(['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm','video/mp4']);
    recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : {});
    recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };

    recorder.onstop = () => {
      clearInterval(timerInt);
      const blobMime = recorder.mimeType;
      const ext      = blobMime.includes('webm') ? 'webm' : 'mp4';
      const blob     = new Blob(chunks, { type: blobMime });
      const file     = Object.assign(new File([blob], `video_${Date.now()}.${ext}`, { type: blobMime }),
                                     { _duration: elapsed });

      /* Snapshot de la prévisualisation comme miniature */
      const c = document.createElement('canvas'); c.width = 320; c.height = 180;
      c.getContext('2d').drawImage(preview, 0, 0, 320, 180);
      c.toBlob(thumb => {
        const f = Object.assign(file, { _thumbBlob: thumb });
        window._addCapturedFile(f, 'video');
      }, 'image/jpeg', .8);

      btnRecord.disabled = false; btnStop.disabled = true;
      if (timerEl) timerEl.textContent = '00:00';
    };

    recorder.start(500);
    btnRecord.disabled = true; btnStop.disabled = false;
    timerInt = setInterval(() => {
      elapsed++;
      if (timerEl) timerEl.textContent = formatTime(elapsed);
    }, 1000);
  });

  btnStop.addEventListener('click', () => recorder?.stop());
}


/* ══════════════════════════════════════════════════════════
   6. ENREGISTREMENT AUDIO
   ══════════════════════════════════════════════════════════ */

function initAudioCapture() {
  const timerEl   = document.getElementById('audio-rec-timer');
  const waveform  = document.getElementById('audio-waveform');
  const btnRecord = document.getElementById('btn-record-audio');
  const btnStop   = document.getElementById('btn-stop-audio');
  const bars      = waveform ? Array.from(waveform.querySelectorAll('.waveform-bar')) : [];
  if (!btnRecord) return;

  let stream = null, recorder = null, chunks = [], elapsed = 0, timerInt = null;
  let analyser = null, animFrame = null;

  btnRecord.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      /* Visualiseur fréquences temps réel */
      const actx   = new (window.AudioContext || window.webkitAudioContext)();
      const source = actx.createMediaStreamSource(stream);
      analyser      = actx.createAnalyser(); analyser.fftSize = 64;
      source.connect(analyser);
      animateWave();

      chunks = []; elapsed = 0;
      const mime = bestMime(['audio/webm;codecs=opus','audio/ogg;codecs=opus','audio/mp4']);
      recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : {});
      recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };

      recorder.onstop = () => {
        clearInterval(timerInt); cancelAnimationFrame(animFrame);
        waveform?.classList.remove('recording');
        bars.forEach(b => b.style.height = '8px');
        stream.getTracks().forEach(t => t.stop());

        const blobMime = recorder.mimeType;
        const ext      = blobMime.includes('webm') ? 'webm' : blobMime.includes('mp4') ? 'm4a' : 'ogg';
        const file     = Object.assign(
          new File([new Blob(chunks, { type: blobMime })], `vocal_${Date.now()}.${ext}`, { type: blobMime }),
          { _duration: elapsed }
        );
        window._addCapturedFile(file, 'audio');
        btnRecord.disabled = false; btnStop.disabled = true;
        if (timerEl) timerEl.textContent = '00:00';
      };

      recorder.start(500);
      waveform?.classList.add('recording');
      btnRecord.disabled = true; btnStop.disabled = false;
      timerInt = setInterval(() => {
        elapsed++;
        if (timerEl) timerEl.textContent = formatTime(elapsed);
      }, 1000);

    } catch (err) { alert(`Microphone inaccessible : ${err.message}`); }
  });

  btnStop.addEventListener('click', () => recorder?.stop());

  function animateWave() {
    if (!analyser || !bars.length) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    function draw() {
      analyser.getByteFrequencyData(data);
      bars.forEach((b, i) => { b.style.height = Math.max(4, (data[i % data.length] || 0) * 56 / 255) + 'px'; });
      animFrame = requestAnimationFrame(draw);
    }
    draw();
  }
}

/* ── Utilitaires ── */
function bestMime(types) { return types.find(t => MediaRecorder.isTypeSupported(t)) || ''; }
function formatTime(s)   { return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`; }


/* ══════════════════════════════════════════════════════════
   7. PAGE GALERIE — items mixtes + scroll infini + temps réel
   ══════════════════════════════════════════════════════════ */

function initGalleryPage() {
  const grid        = document.getElementById('gallery-grid');
  const loader      = document.getElementById('gallery-loader');
  const empty       = document.getElementById('gallery-empty');
  const filterTable = document.getElementById('filter-table');
  const filterDate  = document.getElementById('filter-date');
  const resetBtn    = document.getElementById('reset-filters');
  const toggleSlide = document.getElementById('toggle-slideshow');
  const typeBtns    = document.querySelectorAll('.filter-type-btn');

  let allItems    = [], currentPage = 1, hasNext = true;
  let loading     = false, lastId = 0, activeType = 'all';

  loadItems();

  /* Scroll infini */
  window.addEventListener('scroll', () => {
    if (loading || !hasNext) return;
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 400) {
      currentPage++;
      loadItems();
    }
  });

  /* Filtres type */
  typeBtns.forEach(btn => btn.addEventListener('click', () => {
    typeBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeType = btn.dataset.type;
    resetAndReload();
  }));

  filterTable.addEventListener('change', resetAndReload);
  filterDate.addEventListener('change',  resetAndReload);
  resetBtn.addEventListener('click', () => {
    filterTable.value = ''; filterDate.value = '';
    typeBtns.forEach(b => b.classList.remove('active'));
    typeBtns[0]?.classList.add('active');
    activeType = 'all';
    resetAndReload();
  });

  function resetAndReload() {
    currentPage = 1; hasNext = true; allItems = []; lastId = 0;
    grid.innerHTML = ''; empty.style.display = 'none';
    loadItems();
  }

  function apiParams(extra = {}) {
    return new URLSearchParams({
      page:  currentPage,
      table: filterTable.value,
      date:  filterDate.value,
      types: activeType === 'all' ? 'photo,video,audio' : activeType,
      ...extra,
    }).toString();
  }

  function loadItems() {
    if (loading) return;
    loading = true; loader.style.display = 'flex';
    fetch(`${window.GALLERY_DATA_URL}?${apiParams()}`)
      .then(r => r.json())
      .then(data => {
        loader.style.display = 'none'; loading = false; hasNext = data.has_next;
        if (!data.photos.length && !allItems.length) { empty.style.display = 'block'; return; }
        data.photos.forEach(item => { allItems.push(item); if (item.id > lastId) lastId = item.id; renderItem(item); });
      })
      .catch(() => { loader.style.display = 'none'; loading = false; });
  }

  /* Temps réel */
  setInterval(() => {
    if (!lastId) return;
    fetch(`${window.GALLERY_DATA_URL}?${apiParams({ since_id: lastId })}`)
      .then(r => r.json())
      .then(data => {
        if (!data.photos?.length) return;
        data.photos.slice().reverse().forEach(item => {
          if (item.id <= lastId) return;
          lastId = item.id; allItems.unshift(item);
          renderItem(item, true); empty.style.display = 'none';
        });
      }).catch(() => {});
  }, REALTIME_INTERVAL);

  /* ── Rendu d'un item ── */
  function renderItem(item, prepend = false) {
    const el = document.createElement('div');
    el.className = 'gallery-item';
    el.dataset.id = item.id; el.dataset.type = item.type;
    el.setAttribute('role', 'listitem');
    el.setAttribute('tabindex', '0');
    el.setAttribute('aria-label', `${item.type === 'photo' ? 'Photo' : item.type === 'video' ? 'Vidéo' : 'Audio'} de ${item.auteur}`);

    if      (item.type === 'photo') buildPhotoItem(el, item);
    else if (item.type === 'video') buildVideoItem(el, item);
    else                            buildAudioItem(el, item);

    const cap = document.createElement('div');
    cap.className   = 'gallery-item-caption';
    cap.textContent = `${item.auteur}${item.table ? ' · ' + item.table : ''}`;
    el.appendChild(cap);

    el.addEventListener('click',   () => openLightbox(item.id));
    el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') openLightbox(item.id); });

    prepend ? grid.insertBefore(el, grid.firstChild) : grid.appendChild(el);
  }

  function buildPhotoItem(el, item) {
    const img = document.createElement('img');
    img.src = item.thumbnail_url; img.loading = 'lazy'; img.alt = '';
    img.className = 'gallery-thumb-img';
    el.appendChild(img);
  }

  function buildVideoItem(el, item) {
    /* Miniature statique */
    const img = document.createElement('img');
    img.className = 'gallery-thumb-img'; img.loading = 'lazy'; img.alt = '';
    if (item.thumbnail_url) {
      img.src = item.thumbnail_url;
    } else {
      img.style.display = 'none';
      el.style.background = 'linear-gradient(135deg,#3d2b1f,#6b4f3a)';
    }
    el.appendChild(img);

    const badge = document.createElement('span');
    badge.className = 'gallery-type-badge'; badge.textContent = '▶ Vidéo';
    el.appendChild(badge);

    /* Vidéo hover : 5 premières secondes, muet */
    const hv = document.createElement('video');
    hv.className = 'hover-video'; hv.src = item.file_url;
    hv.muted = true; hv.loop = false; hv.preload = 'none'; hv.playsInline = true;
    el.appendChild(hv);

    el.addEventListener('mouseenter', () => {
      hv.currentTime = 0; hv.play().catch(() => {});
      hv._t = setTimeout(() => hv.pause(), 5000);
    });
    el.addEventListener('mouseleave', () => { clearTimeout(hv._t); hv.pause(); hv.currentTime = 0; });
  }

  function buildAudioItem(el, item) {
    el.classList.add('gallery-item--audio');
    const icon = document.createElement('div');
    icon.className = 'audio-gallery-icon'; icon.textContent = '🎵';
    const barsWrap = document.createElement('div');
    barsWrap.className = 'audio-gallery-bars';
    for (let i = 0; i < 8; i++) {
      const b = document.createElement('span');
      b.style.height = (4 + Math.random() * 18) + 'px';
      barsWrap.appendChild(b);
    }
    el.append(icon, barsWrap);
  }


  /* ══════════════════════════════════════════════════════════
     8. LIGHTBOX — image / vidéo / audio + swipe + drag
     ══════════════════════════════════════════════════════════ */

  const lightbox  = document.getElementById('lightbox');
  const mediaWrap = document.getElementById('lightbox-media-wrap');
  const caption   = document.getElementById('lightbox-caption');
  const btnClose  = document.getElementById('lightbox-close');
  const btnPrev   = document.getElementById('lightbox-prev');
  const btnNext   = document.getElementById('lightbox-next');

  let currentIndex = 0;

  function openLightbox(itemId) {
    currentIndex = allItems.findIndex(i => i.id === itemId);
    if (currentIndex === -1) return;
    showCurrent();
    lightbox.style.display       = 'flex';
    document.body.style.overflow = 'hidden';
    btnClose.focus();
  }

  function closeLightbox() {
    mediaWrap.querySelector('video')?.pause();
    mediaWrap.querySelector('audio')?.pause();
    lightbox.style.display       = 'none';
    document.body.style.overflow = '';
    stopSlideshow();
  }

  function showCurrent() {
    const item = allItems[currentIndex];
    if (!item) return;
    mediaWrap.querySelector('video')?.pause();
    mediaWrap.querySelector('audio')?.pause();
    mediaWrap.innerHTML = '';

    if (item.type === 'photo') {
      const img = document.createElement('img');
      img.src = item.full_url; img.alt = `Photo de ${item.auteur}`;
      mediaWrap.appendChild(img);

    } else if (item.type === 'video') {
      const v = document.createElement('video');
      v.src = item.file_url; v.controls = true; v.autoplay = true; v.playsInline = true;
      v.style.cssText = 'max-width:92vw;max-height:80vh;';
      mediaWrap.appendChild(v);

    } else {
      const wrap = document.createElement('div');
      wrap.className = 'lightbox-audio-wrapper';
      const icon = document.createElement('div');
      icon.className = 'lightbox-audio-icon'; icon.textContent = '🎵';
      const name = document.createElement('p');
      name.style.cssText = 'color:white;font-size:.9rem;'; name.textContent = item.auteur;
      const a = document.createElement('audio');
      a.src = item.file_url; a.controls = true; a.autoplay = true;
      a.style.width = 'min(380px,88vw)';
      wrap.append(icon, name, a);
      mediaWrap.appendChild(wrap);
    }

    caption.textContent = `${item.auteur}${item.table ? ' · ' + item.table : ''} — ${item.date_upload}`;
  }

  const goPrev = () => { currentIndex = (currentIndex - 1 + allItems.length) % allItems.length; showCurrent(); };
  const goNext = () => { currentIndex = (currentIndex + 1) % allItems.length; showCurrent(); };

  btnClose.addEventListener('click', closeLightbox);
  btnPrev.addEventListener('click',  goPrev);
  btnNext.addEventListener('click',  goNext);
  lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });

  /* Clavier */
  document.addEventListener('keydown', e => {
    if (lightbox.style.display !== 'flex') return;
    if (e.key === 'Escape')     closeLightbox();
    if (e.key === 'ArrowLeft')  goPrev();
    if (e.key === 'ArrowRight') goNext();
  });

  /* ── Swipe tactile ── */
  let tx0 = 0, ty0 = 0;
  lightbox.addEventListener('touchstart', e => { tx0 = e.touches[0].clientX; ty0 = e.touches[0].clientY; }, { passive: true });
  lightbox.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - tx0;
    const dy = e.changedTouches[0].clientY - ty0;
    if (Math.abs(dx) < SWIPE_THRESHOLD || Math.abs(dy) > Math.abs(dx)) return;
    slideAnim(dx > 0 ? 'right' : 'left');
    dx > 0 ? goPrev() : goNext();
  }, { passive: true });

  /* ── Drag souris ── */
  let mx0 = 0, dragging = false;
  mediaWrap.addEventListener('mousedown', e => { mx0 = e.clientX; dragging = true; mediaWrap.style.cursor = 'grabbing'; e.preventDefault(); });
  window.addEventListener('mousemove', e => { if (!dragging) return; mediaWrap.style.transform = `translateX(${(e.clientX - mx0) * 0.3}px)`; });
  window.addEventListener('mouseup', e => {
    if (!dragging) return;
    dragging = false; mediaWrap.style.cursor = '';
    const dx = e.clientX - mx0;
    if (Math.abs(dx) >= SWIPE_THRESHOLD) {
      slideAnim(dx > 0 ? 'right' : 'left');
      dx > 0 ? goPrev() : goNext();
    } else {
      mediaWrap.style.transition = 'transform .2s ease';
      mediaWrap.style.transform  = 'translateX(0)';
      setTimeout(() => { mediaWrap.style.transition = ''; }, 200);
    }
  });

  function slideAnim(dir) {
    const out = dir === 'left' ? '-70px' : '70px';
    mediaWrap.style.transition = 'transform .22s ease, opacity .22s';
    mediaWrap.style.transform  = `translateX(${out})`;
    mediaWrap.style.opacity    = '0';
    setTimeout(() => {
      mediaWrap.style.transition = '';
      mediaWrap.style.transform  = `translateX(${dir === 'left' ? '70px' : '-70px'})`;
      requestAnimationFrame(() => {
        mediaWrap.style.transition = 'transform .22s ease, opacity .22s';
        mediaWrap.style.transform  = 'translateX(0)';
        mediaWrap.style.opacity    = '1';
        setTimeout(() => { mediaWrap.style.transition = ''; }, 240);
      });
    }, 220);
  }

  /* ══════════════════════════════════════════════════════════
     9. DIAPORAMA
     ══════════════════════════════════════════════════════════ */

  let slideshowTimer = null;

  toggleSlide?.addEventListener('change', () => {
    toggleSlide.checked ? startSlideshow() : stopSlideshow();
  });

  function startSlideshow() {
    if (!allItems.length) return;
    currentIndex = 0; showCurrent();
    lightbox.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    slideshowTimer = setInterval(goNext, 4500);
  }

  function stopSlideshow() {
    clearInterval(slideshowTimer); slideshowTimer = null;
    if (toggleSlide) toggleSlide.checked = false;
  }
}


/* ══════════════════════════════════════════════════════════
   10. PAGE ADMINISTRATION
   ══════════════════════════════════════════════════════════ */

function initAdminPage() {
  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      if (!confirm('Supprimer définitivement ce fichier ?')) return;
      const id   = this.dataset.id;
      const type = this.dataset.type;
      const url  = type === 'photo'
        ? `${window.DELETE_PHOTO_URL}${id}/`
        : `${window.DELETE_MEDIA_URL}${id}/`;

      fetch(url, { method: 'POST', headers: { 'X-CSRFToken': window.CSRF_TOKEN } })
        .then(r => r.json())
        .then(data => {
          if (data.success) document.querySelector(`.admin-card[data-id="${id}"]`)?.remove();
          else alert('Suppression échouée.');
        })
        .catch(() => alert('Erreur réseau.'));
    });
  });
}
```

# 7. Compression (déjà intégrée)

La compression et la génération de miniatures sont gérées dans `gallery/models.py` via `Photo.save()` :

- Correction de l'orientation EXIF
- Redimensionnement à 1920px max (largeur)
- Génération d'une miniature à 400px

Aucun code supplémentaire requis.

# 8. QR Code

## `gallery/management/commands/generate_qrcode.py`

```python 
import os
import qrcode
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Génère le QR Code pointant vers la page d'upload du site mariage."

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default=None,
            help="URL personnalisée (par défaut : SITE_PUBLIC_URL/upload/)"
        )

    def handle(self, *args, **options):
        url = options['url'] or f"{settings.SITE_PUBLIC_URL}/upload/"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#b08d4f", back_color="white")

        qr_dir = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
        os.makedirs(qr_dir, exist_ok=True)

        qr_path = os.path.join(qr_dir, 'qrcode.png')
        img.save(qr_path)

        self.stdout.write(self.style.SUCCESS(f"QR Code généré : {qr_path}"))
        self.stdout.write(self.style.SUCCESS(f"URL encodée : {url}"))
```

Génération du QR Code (à exécuter après configuration du domaine) :

```bash
source venv/bin/activate
python manage.py generate_qrcode
```

Le QR Code pointe vers `/upload/` directement : l'invité scanne → arrive sur le formulaire → saisit son nom → sélectionne ses photos.

# 9. Administration

Déjà implémentée : `/admin-gallery/` (suppression, téléchargement individuel, téléchargement ZIP, affichage du QR Code) + interface Django native `/admin/`.

Création du compte administrateur :

```bash 
source venv/bin/activate
python manage.py createsuperuser
```

# 10. Nginx

## /etc/nginx/sites-available/mariage


```nginx
server {
    listen 80;
    server_name photos-mariage.mondomaine.fr localhost 127.0.0.1;

    client_max_body_size 60M;

    access_log /var/log/nginx/mariage_access.log;
    error_log /var/log/nginx/mariage_error.log;

    location /static/ {
        alias /home/pi/mariage/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias /home/pi/mariage/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://unix:/run/gunicorn-mariage.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
    }
}
```

```bash
mkdir -p deploy
```

```bash
cat > /deploy/nginx-mariage.conf << 'EOF'
server {
    listen 80;
    server_name localhost 127.0.0.1;

    client_max_body_size 60M;

    location /static/ {
        alias /mnt/mariage_data/BibiUnion/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /mnt/mariage_data/BibiUnion/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn-mariage.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
    }
}
EOF
```

Activation :

```bash 
sudo ln -s /etc/nginx/sites-available/mariage /etc/nginx/sites-enabled/mariage
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

# 11. Gunicorn

## /etc/systemd/system/gunicorn-mariage.socket

```ìni 
[Unit]
Description=Socket Gunicorn pour mariage

[Socket]
ListenStream=/run/gunicorn-mariage.sock
SocketUser=www-data
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
```


```bash
cat > /deploy/gunicorn-mariage.socket << 'EOF'
[Unit]
Description=Socket Gunicorn pour mariage

[Socket]
ListenStream=/run/gunicorn-mariage.sock
SocketUser=www-data
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
EOF
```


## /etc/systemd/system/gunicorn-mariage.service

```ìni 
[Unit]
Description=Gunicorn daemon pour le site mariage
Requires=gunicorn-mariage.socket
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/mariage
ExecStart=/home/pi/mariage/venv/bin/gunicorn \
          --access-logfile /home/pi/mariage/logs/gunicorn-access.log \
          --error-logfile /home/pi/mariage/logs/gunicorn-error.log \
          --workers 2 \
          --timeout 120 \
          --bind unix:/run/gunicorn-mariage.sock \
          mariage.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
cat > /deploy/gunicorn-mariage.service << 'EOF'
[Unit]
Description=Gunicorn daemon pour le site mariage
Requires=gunicorn-mariage.socket
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/mnt/mariage_data/BibiUnion
ExecStart=/mnt/mariage_data/BibiUnion/venv/bin/gunicorn \
          --access-logfile /mnt/mariage_data/BibiUnion/logs/gunicorn-access.log \
          --error-logfile /mnt/mariage_data/BibiUnion/logs/gunicorn-error.log \
          --workers 2 \
          --timeout 120 \
          --bind unix:/run/gunicorn-mariage.sock \
          mariage.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
```


Activation :

```bash 
mkdir -p /mnt/mariage_data/BibiUnion/logs
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-mariage.socket
sudo systemctl enable --now gunicorn-mariage.service
sudo systemctl status gunicorn-mariage.service
```

# 12. Cloudflare Tunnel — Guide complet

## 12.1 Création du compte Cloudflare

1. Aller sur (https://dash.cloudflare.com) et créer un compte gratuit.
2. Ajouter votre domaine (`mondomaine.fr`) — suivre les instructions pour changer les serveurs DNS chez votre registrar vers ceux fournis par Cloudflare.
3. Attendre l'activation du domaine (DNS propagé, peut prendre jusqu'à 24h, souvent quelques minutes).

## 12.2 Installation de cloudflared sur le Raspberry Pi

```bash
# Raspberry Pi 2 B = architecture ARM (armhf généralement, vérifier avec `uname -m`)
uname -m
# Si armv7l :
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-armhf.deb
# Si aarch64 (64 bits) :
# curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb

sudo dpkg -i cloudflared.deb
cloudflared --version
```

## 12.3 Authentification et création du tunnel

```bash 
# Connexion au compte Cloudflare (ouvre un lien à copier dans un navigateur)
cloudflared tunnel login

# Création du tunnel nommé "mariage"
cloudflared tunnel create mariage

# Note l'UUID du tunnel affiché, ex : 1234abcd-5678-efgh-9012-ijklmnopqrst
# Un fichier de credentials est créé dans ~/.cloudflared/<UUID>.json
```

## 12.4 Configuration du tunnel
Créer le fichier `~/.cloudflared/config.yml` :

```yaml
tunnel: 1234abcd-5678-efgh-9012-ijklmnopqrst
credentials-file: /home/pi/.cloudflared/1234abcd-5678-efgh-9012-ijklmnopqrst.json

ingress:
  - hostname: photos-mariage.mondomaine.fr
    service: http://localhost:80
  - service: http_status:404
```

Remplacer l'UUID par celui généré à l'étape précédente.

## 12.5 Configuration DNS

```bash 
# Crée automatiquement l'enregistrement CNAME dans Cloudflare DNS
cloudflared tunnel route dns mariage photos-mariage.mondomaine.fr
```

Vérification sur le dashboard Cloudflare (DNS > Records) : un enregistrement `CNAME` vers `<UUID>.cfargotunnel.com` doit apparaître.

## 12.6 Service systemd pour cloudflared (démarrage auto au boot)

```bash 
sudo cloudflared service install
sudo systemctl enable --now cloudflared
sudo systemctl status cloudflared
```

Le fichier `/etc/cloudflared/config.yml` est utilisé par le service. Copier la configuration :

```bash 
sudo mkdir -p /etc/cloudflared
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/config.yml
sudo cp ~/.cloudflared/*.json /etc/cloudflared/
sudo systemctl restart cloudflared
```

## 12.7 Vérification

```bash 
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -f
```

Tester depuis un téléphone (4G/5G, différent du réseau du Pi) : ouvrir `https://photos-mariage.mondomaine.fr/upload/`.

**Avantage clé** : l'URL reste identique même si le Raspberry change de réseau (Wi-Fi maison → partage de connexion), car le tunnel est une connexion sortante initiée par le Pi — aucune redirection de port ni IP fixe nécessaire.

## 12.8 Start_tunnel

```bash
#!/bin/bash

SETTINGS="/mnt/mariage_data/BibiUnion/mariage/settings.py"

echo "Démarrage du tunnel Cloudflare..."

# Lance cloudflared en arrière-plan et capture l'URL
cloudflared tunnel --url http://localhost:80 2>&1 &
TUNNEL_PID=$!

# Attend que l'URL apparaisse dans les logs
URL=""
echo "En attente de l'URL du tunnel..."
while [ -z "$URL" ]; do
    sleep 2
    URL=$(curl -s http://127.0.0.1:20241/metrics 2>/dev/null | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1)
done

echo "URL détectée : $URL"
HOSTNAME=$(echo $URL | sed 's|https://||')

# Met à jour settings.py
sed -i "s|'[^']*\.trycloudflare\.com'|'$HOSTNAME'|g" "$SETTINGS"
sed -i "s|SITE_PUBLIC_URL = '.*'|SITE_PUBLIC_URL = '$URL'|g" "$SETTINGS"

echo "settings.py mis à jour avec : $HOSTNAME"

# Redémarre gunicorn
sudo systemctl restart gunicorn-mariage
echo "Gunicorn redémarré ✅"

# Régénère le QR Code avec la nouvelle URL
cd /mnt/mariage_data/BibiUnion
source venv/bin/activate
python manage.py generate_qrcode
echo "QR Code régénéré ✅"

echo ""
echo "========================================"
echo "  Site accessible sur : $URL/upload/"
echo "========================================"

# Garde le tunnel en premier plan
wait $TUNNEL_PID
```

## `./start_tunnel.sh`

```bash
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
if systemctl is-active --quiet gunicorn-mariage 2>/dev/null; then
    sudo systemctl restart gunicorn-mariage
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
python manage.py generate_qrcode
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

# ── Résumé ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅  Site en ligne !                     ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Upload  : $URL/upload/"
echo "║  Galerie : $URL/gallery/"
echo "║  QR Code : $URL/qrcode/"
echo "║  Admin   : $URL/admin-gallery/"
echo "╚══════════════════════════════════════════╝"
echo ""

# Garde le tunnel actif
wait $TUNNEL_PID

```


```bash
cat > ./start_tunnel.sh << 'EOF'
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
if systemctl is-active --quiet gunicorn-mariage 2>/dev/null; then
    sudo systemctl restart gunicorn-mariage
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
python manage.py generate_qrcode
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

# ── Résumé ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅  Site en ligne !                     ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Upload  : $URL/upload/"
echo "║  Galerie : $URL/gallery/"
echo "║  QR Code : $URL/qrcode/"
echo "║  Admin   : $URL/admin-gallery/"
echo "╚══════════════════════════════════════════╝"
echo ""

# Garde le tunnel actif
wait $TUNNEL_PID

```


Utilisation

```bash
chmod +x ./start_tunnel.sh
sudo ./start_tunnel.sh
```


# 13. Installation Raspberry Pi

## `setup.py`

```python
#!/usr/bin/env python3
"""
setup.py — Configuration interactive multi-plateforme
BibiUnion Mariage

Lance ce script une fois après avoir cloné le projet.
Il détecte ou te demande la plateforme cible, adapte les chemins,
génère les fichiers de service systemd, et met à jour settings.py.

Usage :
    python setup.py
    python setup.py --platform rpi4
    python setup.py --platform mac
"""

import argparse
import os
import platform
import re
import sys
from pathlib import Path

# ── Couleurs terminal ─────────────────────────────────────────────────────────
GREEN  = '\033[92m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
RED    = '\033[91m'
RESET  = '\033[0m'
BOLD   = '\033[1m'

def p(msg, color=RESET):     print(f"{color}{msg}{RESET}")
def ok(msg):                  p(f"  ✅  {msg}", GREEN)
def warn(msg):                p(f"  ⚠️   {msg}", YELLOW)
def info(msg):                p(f"  ℹ️   {msg}", BLUE)
def err(msg):                 p(f"  ❌  {msg}", RED)

# ── Config par plateforme ─────────────────────────────────────────────────────

PLATFORMS = {
    'rpi2b': {
        'label':            'Raspberry Pi 2 B (1 Go RAM, ARM 32 bits)',
        'default_root':     '/mnt/mariage_data/BibiUnion',
        'gunicorn_workers': 1,
        'gunicorn_timeout': 180,
        'max_video_mb':     300,
        'max_audio_mb':     30,
        'service_user':     'pi',
        'nginx_client_max': '320M',
    },
    'rpi4': {
        'label':            'Raspberry Pi 4 (4+ Go RAM, ARM 64 bits)',
        'default_root':     '/mnt/mariage_data/BibiUnion',
        'gunicorn_workers': 2,
        'gunicorn_timeout': 120,
        'max_video_mb':     500,
        'max_audio_mb':     50,
        'service_user':     'pi',
        'nginx_client_max': '520M',
    },
    'mac': {
        'label':            'macOS (développement local)',
        'default_root':     str(Path(__file__).resolve().parent),
        'gunicorn_workers': 2,
        'gunicorn_timeout': 60,
        'max_video_mb':     500,
        'max_audio_mb':     50,
        'service_user':     os.environ.get('USER', 'user'),
        'nginx_client_mac': '520M',
    },
}

STORAGE_OPTIONS = {
    '1': ('Carte SD / stockage interne',  None),          # None = utilise project_root
    '2': ('Disque USB (par défaut /mnt/usb/mariage)', '/mnt/usb/mariage'),
    '3': ('Chemin personnalisé',           '__custom__'),
}


def detect_platform():
    s = platform.system()
    if s == 'Darwin':
        return 'mac'
    try:
        model = Path('/proc/device-tree/model').read_text()
        if 'Pi 4' in model or 'Pi 5' in model:
            return 'rpi4'
        return 'rpi2b'
    except Exception:
        return 'rpi2b'


def ask_platform():
    p(f"\n{BOLD}── Choix de la plateforme ──────────────────────────{RESET}")
    detected = detect_platform()
    info(f"Plateforme détectée automatiquement : {detected}")
    for key, cfg in PLATFORMS.items():
        marker = ' ← détectée' if key == detected else ''
        print(f"  [{key}] {cfg['label']}{marker}")
    choice = input(f"\nPlateforme [{detected}] : ").strip().lower() or detected
    if choice not in PLATFORMS:
        warn(f"Choix invalide, utilisation de : {detected}")
        choice = detected
    return choice


def ask_storage(project_root):
    p(f"\n{BOLD}── Localisation du stockage des médias ─────────────{RESET}")
    for key, (label, path) in STORAGE_OPTIONS.items():
        default_path = os.path.join(project_root, 'media') if path is None else path
        print(f"  [{key}] {label}  →  {default_path}")
    choice = input("\nChoix [1] : ").strip() or '1'
    label, path = STORAGE_OPTIONS.get(choice, STORAGE_OPTIONS['1'])

    if path is None:
        media_root = os.path.join(project_root, 'media')
    elif path == '__custom__':
        media_root = input("Chemin absolu du dossier de stockage : ").strip()
        if not media_root:
            media_root = os.path.join(project_root, 'media')
    else:
        media_root = path

    ok(f"Stockage des médias : {media_root}")
    return media_root


def ask_domain():
    p(f"\n{BOLD}── Domaine public ──────────────────────────────────{RESET}")
    info("Laissez vide pour utiliser le tunnel temporaire (start_tunnel.sh le mettra à jour).")
    domain = input("Domaine fixe (ex: photos.bibiunion.fr) ou vide : ").strip()
    if domain:
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        ok(f"Domaine : {domain}")
    else:
        domain = 'https://placeholder.trycloudflare.com'
        info("Domaine placeholder — start_tunnel.sh le remplacera au démarrage.")
    return domain


def update_settings(project_root, media_root, platform_key, domain):
    settings_path = os.path.join(project_root, 'mariage', 'settings.py')
    if not os.path.isfile(settings_path):
        err(f"settings.py introuvable : {settings_path}")
        return False

    cfg = PLATFORMS[platform_key]

    with open(settings_path, 'r') as f:
        content = f.read()

    # Variable d'env de plateforme
    content = re.sub(
        r"os\.environ\.get\('MARIAGE_PLATFORM'.*?\)",
        f"os.environ.get('MARIAGE_PLATFORM', '{platform_key}')",
        content
    )

    # SITE_PUBLIC_URL
    content = re.sub(
        r"SITE_PUBLIC_URL\s*=\s*'[^']*'",
        f"SITE_PUBLIC_URL = '{domain}'",
        content
    )

    # Domaine dans ALLOWED_HOSTS
    hostname = domain.replace('https://', '').replace('http://', '')
    if 'ALLOWED_HOSTS' in content and hostname not in content:
        content = content.replace(
            "ALLOWED_HOSTS = [",
            f"ALLOWED_HOSTS = [\n    '{hostname}',"
        )

    # CSRF_TRUSTED_ORIGINS
    if 'CSRF_TRUSTED_ORIGINS' in content and domain not in content:
        content = content.replace(
            "CSRF_TRUSTED_ORIGINS = [",
            f"CSRF_TRUSTED_ORIGINS = [\n    '{domain}',"
        )

    with open(settings_path, 'w') as f:
        f.write(content)

    ok("settings.py mis à jour")
    return True


def create_dirs(project_root, media_root):
    dirs = [
        os.path.join(media_root, 'photos'),
        os.path.join(media_root, 'thumbnails'),
        os.path.join(media_root, 'qrcodes'),
        os.path.join(media_root, 'videos'),
        os.path.join(media_root, 'audios'),
        os.path.join(project_root, 'staticfiles'),
        os.path.join(project_root, 'logs'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    ok(f"Dossiers créés dans {media_root}")


def generate_gunicorn_service(project_root, platform_key):
    cfg  = PLATFORMS[platform_key]
    venv = os.path.join(project_root, 'venv', 'bin', 'gunicorn')
    sock = '/run/gunicorn-mariage.sock'
    logs = os.path.join(project_root, 'logs')

    service = f"""[Unit]
Description=Gunicorn daemon pour le site mariage ({platform_key})
Requires=gunicorn-mariage.socket
After=network.target

[Service]
User={cfg['service_user']}
Group=www-data
WorkingDirectory={project_root}
ExecStart={venv} \\
          --access-logfile {logs}/gunicorn-access.log \\
          --error-logfile {logs}/gunicorn-error.log \\
          --workers {cfg['gunicorn_workers']} \\
          --timeout {cfg['gunicorn_timeout']} \\
          --bind unix:{sock} \\
          mariage.wsgi:application

[Install]
WantedBy=multi-user.target
"""
    deploy_dir = os.path.join(project_root, 'deploy')
    os.makedirs(deploy_dir, exist_ok=True)
    path = os.path.join(deploy_dir, 'gunicorn-mariage.service')
    with open(path, 'w') as f:
        f.write(service)
    ok(f"gunicorn-mariage.service généré ({cfg['gunicorn_workers']} worker(s), timeout {cfg['gunicorn_timeout']}s)")
    return path


def generate_nginx_conf(project_root, media_root, platform_key):
    cfg       = PLATFORMS[platform_key]
    static_root = os.path.join(project_root, 'staticfiles')
    max_body  = cfg.get('nginx_client_max', '520M')

    conf = f"""server {{
    listen 80;
    server_name localhost 127.0.0.1;

    # Taille max upload (photo + vidéo)
    client_max_body_size {max_body};

    access_log /var/log/nginx/mariage_access.log;
    error_log  /var/log/nginx/mariage_error.log;

    location /static/ {{
        alias {static_root}/;
        expires 30d;
        add_header Cache-Control "public";
    }}

    location /media/ {{
        alias {media_root}/;
        expires 7d;
        add_header Cache-Control "public";

        # Streaming vidéo : supporte les requêtes Range (seek dans le lecteur)
        add_header Accept-Ranges bytes;
    }}

    location / {{
        proxy_pass http://unix:/run/gunicorn-mariage.sock;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
        # Nécessaire pour les gros uploads vidéo
        proxy_request_buffering off;
    }}
}}
"""
    deploy_dir = os.path.join(project_root, 'deploy')
    os.makedirs(deploy_dir, exist_ok=True)
    path = os.path.join(deploy_dir, 'nginx-mariage.conf')
    with open(path, 'w') as f:
        f.write(conf)
    ok(f"nginx-mariage.conf généré (client_max_body_size: {max_body}, streaming vidéo activé)")
    return path


def print_next_steps(project_root, platform_key):
    p(f"\n{BOLD}{'='*55}{RESET}")
    p(f"{BOLD}  Configuration terminée ! Prochaines étapes :{RESET}")
    p(f"{'='*55}")
    steps = [
        f"cd {project_root}",
        "python3 -m venv venv && source venv/bin/activate",
        "pip install -r requirements.txt",
        "pip install libmagic  # si non installé système",
        "python manage.py migrate",
        "python manage.py collectstatic --noinput",
        "python manage.py createsuperuser",
    ]
    if platform_key != 'mac':
        steps += [
            "sudo cp deploy/gunicorn-mariage.socket /etc/systemd/system/",
            "sudo cp deploy/gunicorn-mariage.service /etc/systemd/system/",
            "sudo cp deploy/nginx-mariage.conf /etc/nginx/sites-available/mariage",
            "sudo ln -sf /etc/nginx/sites-available/mariage /etc/nginx/sites-enabled/mariage",
            "sudo systemctl daemon-reload && sudo systemctl enable --now gunicorn-mariage.socket gunicorn-mariage.service",
            "sudo systemctl restart nginx",
            "sudo ./start_tunnel.sh",
        ]
    else:
        steps += [
            "source venv/bin/activate",
            "python manage.py runserver 0.0.0.0:8000  # dev local",
        ]
    for i, s in enumerate(steps, 1):
        print(f"  {i:2}. {BLUE}{s}{RESET}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Configuration BibiUnion Mariage')
    parser.add_argument('--platform', choices=PLATFORMS.keys(), help='Plateforme cible')
    parser.add_argument('--yes', action='store_true', help='Accepte les valeurs par défaut sans interaction')
    args = parser.parse_args()

    p(f"\n{BOLD}╔══════════════════════════════════════════╗{RESET}")
    p(f"{BOLD}║   BibiUnion — Setup multi-plateforme     ║{RESET}")
    p(f"{BOLD}╚══════════════════════════════════════════╝{RESET}\n")

    platform_key = args.platform or ask_platform()
    info(f"Plateforme sélectionnée : {PLATFORMS[platform_key]['label']}")

    project_root = PLATFORMS[platform_key]['default_root']
    if not args.yes:
        custom = input(f"\nDossier projet [{project_root}] : ").strip()
        if custom:
            project_root = custom

    media_root = ask_storage(project_root) if not args.yes else os.path.join(project_root, 'media')
    domain     = ask_domain() if not args.yes else 'https://placeholder.trycloudflare.com'

    p(f"\n{BOLD}── Génération de la configuration ──────────────────{RESET}")
    create_dirs(project_root, media_root)
    update_settings(project_root, media_root, platform_key, domain)
    generate_gunicorn_service(project_root, platform_key)
    generate_nginx_conf(project_root, media_root, platform_key)

    print_next_steps(project_root, platform_key)


if __name__ == '__main__':
    main()

```

## `install.sh`

```bash 
#!/bin/bash
set -e

echo "=========================================="
echo "  Installation - Application Mariage"
echo "=========================================="

PROJECT_DIR="/mnt/mariage_data/BibiUnion"
VENV_DIR="$PROJECT_DIR/venv"

# ============================================
# 1. Mise à jour système et dépendances
# ============================================
echo "[1/8] Mise à jour du système..."
sudo apt update
sudo apt upgrade -y

echo "[2/8] Installation des paquets système..."
sudo apt install -y python3 python3-pip python3-venv nginx git \
    libjpeg-dev zlib1g-dev libwebp-dev libheif-dev \
    build-essential libssl-dev libffi-dev

# ============================================
# 2. Création de l'environnement virtuel
# ============================================
echo "[3/8] Création de l'environnement virtuel..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

# ============================================
# 3. Installation des dépendances Python
# ============================================
echo "[4/8] Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# ============================================
# 4. Configuration Django
# ============================================
echo "[5/8] Configuration de la base de données..."
mkdir -p media/photos media/thumbnails media/qrcodes staticfiles logs
python manage.py makemigrations gallery
python manage.py migrate
python manage.py collectstatic --noinput

echo ""
echo "Création du compte administrateur :"
python manage.py createsuperuser

# ============================================
# 5. Génération du QR Code
# ============================================
echo "[6/8] Génération du QR Code..."
python manage.py generate_qrcode

# ============================================
# 6. Configuration des permissions
# ============================================
echo "[7/8] Configuration des permissions..."
sudo chown -R pi:www-data "$PROJECT_DIR"
sudo chmod -R 750 "$PROJECT_DIR"
sudo chmod -R 770 "$PROJECT_DIR/media"

# ============================================
# 7. Configuration Gunicorn + Nginx
# ============================================
echo "[8/8] Configuration de Gunicorn et Nginx..."

sudo cp deploy/gunicorn-mariage.socket /etc/systemd/system/
sudo cp deploy/gunicorn-mariage.service /etc/systemd/system/
sudo cp deploy/nginx-mariage.conf /etc/nginx/sites-available/mariage

sudo ln -sf /etc/nginx/sites-available/mariage /etc/nginx/sites-enabled/mariage
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-mariage.socket
sudo systemctl enable --now gunicorn-mariage.service

sudo nginx -t
sudo systemctl restart nginx

echo "=========================================="
echo "  Installation terminée !"
echo "=========================================="
echo ""
echo "Étapes suivantes :"
echo "1. Configurer Cloudflare Tunnel (voir README.md section 12)"
echo "2. Mettre à jour ALLOWED_HOSTS et SITE_PUBLIC_URL dans settings.py"
echo "3. Régénérer le QR Code : python manage.py generate_qrcode"
echo "4. Tester l'accès depuis un téléphone en 4G"
```

```bash
chmod +x install.sh
```

> Remarque : créez les sous-dossiers `deploy/` avec les fichiers `gunicorn-mariage.socket`, `gunicorn-mariage.service, nginx-mariage.conf` listés aux sections 10 et 11 avant d'exécuter `install.sh`.

```bash 
mkdir -p deploy
# copier le contenu des sections 10 et 11 dans :
# deploy/nginx-mariage.conf
# deploy/gunicorn-mariage.socket
# deploy/gunicorn-mariage.service
```

# Déploiement complet — séquence de commandes

```bash 
# 1. Cloner / copier le projet sur le Pi
cd /mnt/mariage_data/
[ -d BibiUnion ] && rm -rf BibiUnion
git clone https://github.com/THEMEZE/BibiUnion.git   # ou scp depuis votre PC
cd BibiUnion

#cd /mnt/mariage_data && rm -rf BibiUnion && git clone https://github.com/THEMEZE/BibiUnion.git && cd BibiUnion

# 2. Lancer l'installation
chmod +x install.sh
./install.sh

# 3. Démarrer le tunnel (à chaque redémarrage du Pi)
chmod +x start_tunnel.sh
sudo ./start_tunnel.sh
```

> `start_tunnel.sh` fait automatiquement : tunnel Cloudflare + mise à jour 
> `settings.py` + redémarrage Gunicorn + régénération du QR Code.

Démarrage automatique au boot (optionnel)

```bash
sudo crontab -e
# Ajouter :
@reboot sleep 15 && /mnt/mariage_data/BibiUnion/start_tunnel.sh >> /mnt/mariage_data/BibiUnion/logs/tunnel.log 2>&1
```

### Si dommain fixe

```bash 
# 3. Configurer Cloudflare Tunnel (section 12)
cloudflared tunnel login
cloudflared tunnel create mariage
nano ~/.cloudflared/config.yml
cloudflared tunnel route dns mariage bibiunion.fr
sudo cloudflared service install
sudo systemctl enable --now cloudflared

# 4. Mettre à jour settings.py avec le vrai domaine, puis :
sudo systemctl restart gunicorn-mariage
sudo systemctl restart nginx
sudo systemctl restart cloudflared

# 5. Régénérer le QR Code avec l'URL finale
source venv/bin/activate
python manage.py generate_qrcode
```

# Tests de validation

```bash 
# 1. Vérifier que Django démarre sans erreur
source venv/bin/activate
python manage.py check

# 2. Vérifier les migrations
python manage.py showmigrations gallery

# 3. Test du serveur de développement (avant Gunicorn)
python manage.py runserver 0.0.0.0:8000
# -> ouvrir http://<IP_du_Pi>:8000/upload/

# 4. Vérifier le statut des services en production
sudo systemctl status gunicorn-mariage.socket
sudo systemctl status gunicorn-mariage.service
sudo systemctl status nginx
sudo systemctl status cloudflared

# 5. Vérifier les logs en cas d'erreur
sudo journalctl -u gunicorn-mariage -n 50 --no-pager
sudo tail -f /var/log/nginx/mariage_error.log
sudo journalctl -u cloudflared -n 50 --no-pager

# 6. Test fonctionnel via curl (en local sur le Pi)
curl -I http://localhost/upload/
curl -I http://localhost/gallery/

# 7. Test fonctionnel via le tunnel (depuis un autre réseau, ex: 4G)
curl -I https://photos-mariage.mondomaine.fr/upload/

# 8. Test d'upload via curl (simulation)
curl -X POST https://photos-mariage.mondomaine.fr/upload/ajax/ \
  -F "image=@test.jpg" \
  -F "auteur=TestUser" \
  -F "table=1" \
  -H "X-CSRFToken: <token recuperé via cookie>"

# 9. Vérifier la génération des miniatures
ls -la media/photos/
ls -la media/thumbnails/

# 10. Test du QR Code
ls -la media/qrcodes/qrcode.png
```

# Procédures de sauvegarde des photos

## Sauvegarde manuelle ponctuelle

```bash
# Sauvegarde complète (media + base de données) vers un disque USB
mkdir -p /mnt/usb/backup_mariage
DATE=$(date +%Y%m%d_%H%M%S)

tar -czf /mnt/usb/backup_mariage/mariage_backup_$DATE.tar.gz \
    /mnt/usb/backup_mariage/media \
    /mnt/usb/backup_mariage/db.sqlite3

echo "Sauvegarde créée : /mnt/usb/backup_mariage/mariage_backup_$DATE.tar.gz"
```

## Script de sauvegarde automatique

Créer `/mnt/mariage_data/backup.sh` :

```bash 
#!/bin/bash
set -e

SOURCE_DIR="/mnt/mariage_data/BibiUnion"
BACKUP_DIR="/mnt/usb/backup_mariage"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# Sauvegarde des médias et de la base
tar -czf "$BACKUP_DIR/mariage_backup_$DATE.tar.gz" \
    "$SOURCE_DIR/media" \
    "$SOURCE_DIR/db.sqlite3"

# Suppression des sauvegardes de plus de 30 jours
find "$BACKUP_DIR" -name "mariage_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Sauvegarde terminée : mariage_backup_$DATE.tar.gz"
```

## Automatisation via cron (sauvegarde quotidienne à 3h du matin)

```bash
crontab -e
```

Ajouter la ligne :

```cron
0 3 * * * /mnt/mariage_data/BibiUnion/backup.sh >> /mnt/mariage_data/BibiUnion/logs/backup.log 2>&1
```

## Restauration

```bash 
# Arrêter les services
sudo systemctl stop gunicorn-mariage

# Restaurer depuis une archive
cd /mnt/mariage_data/BibiUnion
tar -xzf /mnt/usb/backup_mariage/mariage_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Redémarrer
sudo systemctl start gunicorn-mariage
```

# ⚙️ Git Mise à jour

```
git add .
git commit -m "Mise à jour"
git push
```









