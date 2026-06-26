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
