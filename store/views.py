from store.pagination import DefaultPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Discussion, Analysis
from .serializers import (
    DiscussionSerializer,
    DiscussionListSerializer,
    AnalysisSerializer
)


class DiscussionViewSet(ModelViewSet):
    """
    ViewSet pour gérer les discussions TruthBot.
    Chaque utilisateur peut avoir plusieurs discussions.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """
        Retourne uniquement les discussions de l'utilisateur connecté.
        Les administrateurs peuvent voir toutes les discussions.
        """
        user = self.request.user
        queryset = Discussion.objects.prefetch_related('analyses').select_related('user')
        
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        
        return queryset
    
    def get_serializer_class(self):
        """Utilise un serializer simplifié pour la liste"""
        if self.action == 'list':
            return DiscussionListSerializer
        return DiscussionSerializer
    
    def get_serializer_context(self):
        """Passe la requête au serializer"""
        return {'request': self.request}
    
    def perform_create(self, serializer):
        """Assure que la discussion est créée avec l'utilisateur connecté"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='generate-title')
    def generate_title(self, request, pk=None):
        """
        Generate a smart title for the discussion based on its first analysis.
        """
        discussion = self.get_object()
        
        # Get the first analysis
        first_analysis = discussion.analyses.first()
        if not first_analysis:
            return Response(
                {'error': 'No analyses found in this discussion'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate a concise title from the content (max 50 chars)
        content = first_analysis.content
        
        # Simple title generation: take first sentence or first 50 chars
        if '?' in content:
            # If it's a question, use the question
            title = content.split('?')[0] + '?'
        elif '.' in content:
            # Take first sentence
            title = content.split('.')[0]
        else:
            # Just truncate
            title = content[:50]
        
        # Limit to 50 characters
        if len(title) > 50:
            title = title[:47] + '...'
        
        # Update the discussion
        discussion.title = title
        discussion.save()
        
        serializer = self.get_serializer(discussion)
        return Response(serializer.data)


class AnalysisViewSet(ModelViewSet):
    """
    ViewSet pour gérer les analyses (requêtes) dans une discussion.
    Les analyses sont imbriquées dans les discussions.
    """
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['content']
    ordering_fields = ['created_at', 'reliability_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retourne les analyses de la discussion spécifiée.
        Vérifie que l'utilisateur a accès à cette discussion.
        """
        discussion_id = self.kwargs['discussion_pk']
        discussion = get_object_or_404(Discussion, pk=discussion_id)
        
        # Vérifier que l'utilisateur a accès à cette discussion
        user = self.request.user
        if not user.is_staff and discussion.user != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas accès à cette discussion.")
        
        return Analysis.objects.filter(
            discussion=discussion
        ).select_related('discussion', 'discussion__user')
    
    def get_serializer_context(self):
        """
        Passe la discussion et la requête au serializer.
        """
        discussion_id = self.kwargs['discussion_pk']
        discussion = get_object_or_404(Discussion, pk=discussion_id)
        
        # Vérifier les permissions
        user = self.request.user
        if not user.is_staff and discussion.user != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas accès à cette discussion.")
        
        return {
            'request': self.request,
            'discussion': discussion
        }
