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
