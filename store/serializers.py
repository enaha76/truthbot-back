from rest_framework import serializers
from .models import Discussion, Analysis


class AnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer pour les analyses de fiabilité de contenu (TruthBot).
    Génère automatiquement un score de fiabilité aléatoire lors de la création.
    """
    user_id = serializers.SerializerMethodField()
    reliability_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        help_text='Score de fiabilité (0-100)'
    )
    
    class Meta:
        model = Analysis
        fields = [
            'id',
            'user_id',
            'content',
            'content_type',
            'reliability_score',
            'explanation',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'reliability_score', 'explanation', 'created_at', 'updated_at']
    
    def get_user_id(self, obj):
        """Retourne l'ID de l'utilisateur via la discussion"""
        return obj.discussion.user.id
    
    def create(self, validated_data):
        """
        Crée une nouvelle analyse en appelant le service OpenRouter.
        """
        from .services import OpenRouterService
        
        content = validated_data.get('content')
        
        # Appel au service OpenRouter
        try:
            analysis_result = OpenRouterService.analyze_content(content)
            reliability_score = analysis_result['reliability_score']
            explanation = analysis_result['explanation']
        except Exception as e:
            # En cas d'erreur, on peut soit lever une erreur, soit mettre des valeurs par défaut
            # Pour l'instant, on log l'erreur et on met des valeurs nulles ou par défaut
            print(f"Error calling OpenRouter: {e}")
            reliability_score = None
            explanation = f"Erreur lors de l'analyse: {str(e)}"
        
        # Récupérer la discussion depuis le contexte
        discussion = self.context['discussion']
        
        # Créer l'analyse
        analysis = Analysis.objects.create(
            discussion=discussion,
            reliability_score=reliability_score,
            explanation=explanation,
            **validated_data
        )
        
        return analysis


class DiscussionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les discussions TruthBot.
    """
    user_id = serializers.SerializerMethodField()
    analyses_count = serializers.SerializerMethodField()
    analyses = AnalysisSerializer(many=True, read_only=True)
    
    class Meta:
        model = Discussion
        fields = [
            'id',
            'user_id',
            'title',
            'analyses_count',
            'analyses',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'analyses_count', 'created_at', 'updated_at']
    
    def get_user_id(self, obj):
        """Retourne l'ID de l'utilisateur"""
        return obj.user.id if obj.user else None
    
    def get_analyses_count(self, obj):
        """Retourne le nombre d'analyses"""
        return obj.analyses_count


class DiscussionListSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour la liste des discussions (sans les analyses détaillées).
    """
    user_id = serializers.SerializerMethodField()
    analyses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Discussion
        fields = [
            'id',
            'user_id',
            'title',
            'analyses_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'analyses_count', 'created_at', 'updated_at']
    
    def get_user_id(self, obj):
        """Retourne l'ID de l'utilisateur"""
        return obj.user.id if obj.user else None
    
    def get_analyses_count(self, obj):
        """Retourne le nombre d'analyses"""
        return obj.analyses_count
