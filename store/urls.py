from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

# Router principal pour les discussions
router = DefaultRouter()
router.register('discussions', views.DiscussionViewSet, basename='discussions')

# Router imbriqué pour les analyses dans les discussions
discussions_router = routers.NestedDefaultRouter(
    router, 'discussions', lookup='discussion'
)
discussions_router.register(
    'analyses',
    views.AnalysisViewSet,
    basename='discussion-analyses'
)

# URLConf
urlpatterns = router.urls + discussions_router.urls
