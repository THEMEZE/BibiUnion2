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
    'localhost'
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'https://photos.bibiunion.fr',
    'https://*.trycloudflare.com',
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
