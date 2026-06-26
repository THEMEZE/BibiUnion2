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
