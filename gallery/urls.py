from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('',          views.gallery_view, name='gallery'),
    path('upload/',   views.upload_view,  name='upload'),
    path('gallery/',  views.gallery_view, name='gallery'),
    path('qrcode/',   views.qrcode_view,  name='qrcode'),

    # API AJAX — upload
    path('upload/ajax/',       views.upload_ajax,       name='upload_ajax'),
    path('upload/media/ajax/', views.upload_media_ajax, name='upload_media_ajax'),

    # API JSON — galerie mixte
    path('gallery/data/', views.gallery_data, name='gallery_data'),

    # Administration
    path('admin-gallery/',                             views.admin_gallery_view, name='admin_gallery'),
    path('admin-gallery/delete/photo/<int:photo_id>/', views.delete_photo,       name='delete_photo'),
    path('admin-gallery/delete/media/<int:media_id>/', views.delete_media,       name='delete_media'),
    path('admin-gallery/download/photo/<int:photo_id>/', views.download_photo,   name='download_photo'),
    path('admin-gallery/download/media/<int:media_id>/', views.download_media,   name='download_media'),
    path('admin-gallery/download-zip/',                views.download_zip,       name='download_zip'),
]
