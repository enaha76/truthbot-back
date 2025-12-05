from django.conf import settings
from django.db import models


class Discussion(models.Model):
    """
    Modèle pour représenter une discussion entre un utilisateur et TruthBot.
    Chaque utilisateur peut avoir plusieurs discussions, et chaque discussion
    peut contenir plusieurs analyses (requêtes).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discussions'
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Titre optionnel de la discussion'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Discussion'
        verbose_name_plural = 'Discussions'
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
    
    def __str__(self):
        title = self.title or f'Discussion #{self.id}'
        return f'{title} - {self.user.username}'
    
    @property
    def analyses_count(self):
        """Retourne le nombre d'analyses dans cette discussion"""
        return self.analyses.count()


class Analysis(models.Model):
    """
    Modèle pour stocker les analyses de fiabilité de contenu (TruthBot).
    Chaque analyse (requête) appartient à une discussion.
    """
    CONTENT_TYPE_TEXT = 'TEXT'
    CONTENT_TYPE_IMAGE = 'IMAGE'
    CONTENT_TYPE_TWEET = 'TWEET'
    CONTENT_TYPE_ARTICLE = 'ARTICLE'
    
    CONTENT_TYPE_CHOICES = [
        (CONTENT_TYPE_TEXT, 'Texte'),
        (CONTENT_TYPE_IMAGE, 'Image'),
        (CONTENT_TYPE_TWEET, 'Tweet'),
        (CONTENT_TYPE_ARTICLE, 'Article'),
    ]
    
    discussion = models.ForeignKey(
        Discussion,
        on_delete=models.CASCADE,
        related_name='analyses',
        help_text='Discussion à laquelle appartient cette analyse'
    )
    content = models.TextField(help_text='Contenu à analyser (texte, URL, etc.)')
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        default=CONTENT_TYPE_TEXT,
        help_text='Type de contenu analysé'
    )
    reliability_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Score de fiabilité (0-100)',
        null=True,
        blank=True
    )
    explanation = models.TextField(
        help_text="Explication de l'analyse par l'IA",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analyse'
        verbose_name_plural = 'Analyses'
        indexes = [
            models.Index(fields=['discussion', '-created_at']),
        ]
    
    def __str__(self):
        score = f'{self.reliability_score}%' if self.reliability_score else 'N/A'
        return f'Analyse #{self.id} - Discussion #{self.discussion.id} - {score}'
    
    @property
    def user(self):
        """Propriété pour accéder facilement à l'utilisateur via la discussion"""
        return self.discussion.user