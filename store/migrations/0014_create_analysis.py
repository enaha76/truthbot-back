# Generated manually for TruthBot feature

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0013_alter_orderitem_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='Contenu à analyser (texte, URL, etc.)')),
                ('content_type', models.CharField(choices=[('TEXT', 'Texte'), ('IMAGE', 'Image'), ('TWEET', 'Tweet'), ('ARTICLE', 'Article')], default='TEXT', help_text='Type de contenu analysé', max_length=10)),
                ('reliability_score', models.DecimalField(decimal_places=2, help_text='Score de fiabilité (0-100)', max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analyses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Analyse',
                'verbose_name_plural': 'Analyses',
                'ordering': ['-created_at'],
            },
        ),
    ]

