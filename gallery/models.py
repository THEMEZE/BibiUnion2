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
