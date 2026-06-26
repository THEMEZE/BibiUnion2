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
