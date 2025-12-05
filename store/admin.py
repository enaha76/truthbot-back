from django.contrib import admin
from django.db.models import Count
from . import models


@admin.register(models.Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les discussions TruthBot.
    """
    list_display = ['id', 'user', 'title', 'analyses_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    list_per_page = 20
    list_select_related = ['user']
    search_fields = ['title', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('user', 'title')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Annote avec le nombre d'analyses"""
        queryset = super().get_queryset(request)
        return queryset.annotate(analyses_count=Count('analyses'))
    
    def analyses_count(self, obj):
        """Affiche le nombre d'analyses"""
        return obj.analyses_count
    analyses_count.short_description = 'Nombre d\'analyses'


class AnalysisInline(admin.TabularInline):
    """Inline pour afficher les analyses dans une discussion"""
    model = models.Analysis
    extra = 0
    readonly_fields = ['reliability_score', 'created_at']
    fields = ['content', 'content_type', 'reliability_score', 'created_at']


@admin.register(models.Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour les analyses TruthBot.
    Permet de visualiser et gérer les analyses de fiabilité de contenu.
    """
    list_display = ['id', 'discussion', 'content_type', 'reliability_score', 'created_at']
    list_filter = ['content_type', 'created_at']
    list_per_page = 20
    list_select_related = ['discussion', 'discussion__user']
    search_fields = ['content', 'discussion__title', 'discussion__user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('discussion', 'content_type', 'content')
        }),
        ('Résultats', {
            'fields': ('reliability_score',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# Ajouter les analyses inline dans DiscussionAdmin
DiscussionAdmin.inlines = [AnalysisInline]