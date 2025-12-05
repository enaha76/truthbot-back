# Generated manually for TruthBot discussions feature

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_data_forward(apps, schema_editor):
    """Migrer les données : créer une discussion pour chaque analyse existante"""
    Discussion = apps.get_model('store', 'Discussion')
    Analysis = apps.get_model('store', 'Analysis')
    
    # Pour chaque analyse existante, créer une discussion
    for analysis in Analysis.objects.filter(discussion__isnull=True).select_related('user'):
        # Créer une discussion pour cette analyse
        discussion = Discussion.objects.create(
            user=analysis.user,
            title=None
        )
        analysis.discussion = discussion
        analysis.save()


def migrate_data_backward(apps, schema_editor):
    """En cas de rollback, on ne peut pas restaurer le champ user"""
    # En cas de rollback, on ne peut pas restaurer le champ user
    # car on n'a pas cette information stockée
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0014_create_analysis'),
    ]

    operations = [
        # Créer le modèle Discussion
        migrations.CreateModel(
            name='Discussion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text='Titre optionnel de la discussion', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discussions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Discussion',
                'verbose_name_plural': 'Discussions',
                'ordering': ['-updated_at'],
            },
        ),
        # Ajouter l'index pour Discussion
        migrations.AddIndex(
            model_name='discussion',
            index=models.Index(fields=['user', '-updated_at'], name='store_discu_user_id_56bc74_idx'),
        ),
        # Ajouter le champ discussion à Analysis (temporairement nullable)
        migrations.AddField(
            model_name='analysis',
            name='discussion',
            field=models.ForeignKey(
                help_text='Discussion à laquelle appartient cette analyse',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='analyses',
                to='store.discussion'
            ),
        ),
        # Modifier reliability_score pour être nullable
        migrations.AlterField(
            model_name='analysis',
            name='reliability_score',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Score de fiabilité (0-100)',
                max_digits=5,
                null=True
            ),
        ),
        # Migrer les données : créer une discussion pour chaque analyse existante
        migrations.RunPython(
            code=migrate_data_forward,
            reverse_code=migrate_data_backward,
        ),
        # Rendre le champ discussion obligatoire
        migrations.AlterField(
            model_name='analysis',
            name='discussion',
            field=models.ForeignKey(
                help_text='Discussion à laquelle appartient cette analyse',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='analyses',
                to='store.discussion'
            ),
        ),
        # Supprimer l'ancien champ user de Analysis
        migrations.RemoveField(
            model_name='analysis',
            name='user',
        ),
        # Note: L'index composite (discussion, -created_at) sera créé automatiquement
        # par Django si défini dans le modèle. MySQL crée déjà un index pour la FK.
    ]

