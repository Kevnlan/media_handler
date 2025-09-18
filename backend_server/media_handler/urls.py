# media_handler/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MediaViewSet, CollectionViewSet

# Media endpoints under /api/media/
router = DefaultRouter(trailing_slash=False)
router.register(r'', MediaViewSet, basename='media')

# Get the automatically generated URL patterns
router_urls = router.urls

# Filter out the problematic patterns and recreate them with proper slashes
filtered_urls = []
for url_pattern in router_urls:
    # Keep the list view and root view patterns as-is
    if url_pattern.name in ['media-list', 'api-root']:
        filtered_urls.append(url_pattern)

# Manually add the detail and action URLs with proper formatting
from django.urls import re_path

urlpatterns = [
    # List view (no trailing slash)
    path('', MediaViewSet.as_view({'get': 'list', 'post': 'create'}), name='media-list'),
    
    # Detail view with proper slash before pk
    path('/<pk>', MediaViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='media-detail'),
    
    # Custom actions
    path('/<pk>/add-to-collection', 
         MediaViewSet.as_view({'post': 'add_to_collection'}), 
         name='media-add-to-collection'),
    path('/<pk>/remove-from-collection', 
         MediaViewSet.as_view({'post': 'remove_from_collection'}), 
         name='media-remove-from-collection'),

    # Collection routes (no trailing slashes)
    path('/collection',
        CollectionViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='collection-list'
    ),
    path('/collection/<pk>',
        CollectionViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='collection-detail'
    ),
]
