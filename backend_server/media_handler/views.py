"""
media_handler.views

ViewSets and API views for managing Media and Collection resources.
This module exposes:
- MediaViewSet: standard CRUD + custom actions to add/remove media from collections.
- CollectionViewSet: CRUD for user-owned collections.

Authentication: uses a lightweight JWTAuthentication implementation which provides
a user-like object (see `media_handler.auth`).
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Media, Collection
from .serializers import MediaSerializer, CollectionSerializer
from .auth import JWTAuthentication


from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Media, Collection
from .serializers import MediaSerializer, CollectionSerializer
from .auth import JWTAuthentication
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class MediaViewSet(viewsets.ModelViewSet):
    """ViewSet for Media model with proper file upload handling."""
    serializer_class = MediaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at', 'name', 'size']
    search_fields = ['name', 'description']
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Return only media items belonging to the authenticated user and not soft-deleted."""
        queryset = Media.objects.filter(user=self.request.user.id, is_deleted=False)
        media_type = self.request.query_params.get('type')
        if media_type in ['image', 'audio', 'video']:
            queryset = queryset.filter(type=media_type)
        return queryset

    def create(self, request, *args, **kwargs):
        """Override create to add transaction and better error handling."""
        logger.info(f"=== MEDIA UPLOAD REQUEST ===")
        logger.info(f"User: {request.user} (ID: {getattr(request.user, 'id', 'None')})")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Files: {request.FILES}")
        logger.info(f"Content-Type: {request.content_type}")
        
        try:
            with transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                # Save the instance
                instance = serializer.save()
                
                logger.info(f"✅ Successfully created media: {instance.id}")
                logger.info(f"File saved to: {instance.storage_path}")
                logger.info(f"File size: {instance.size}")
                
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, 
                    status=status.HTTP_201_CREATED, 
                    headers=headers
                )
                
        except Exception as e:
            logger.error(f"❌ Error in media upload: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Upload failed: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_destroy(self, instance):
        """Soft-delete: mark the instance as deleted instead of removing from DB."""
        instance.is_deleted = True
        instance.save()
        logger.info(f"Soft-deleted media: {instance.id}")

    @action(detail=True, methods=['post'], url_path='add-to-collection')
    def add_to_collection(self, request, pk=None):
        """Add this media instance to a user's collection."""
        media = self.get_object()
        collection_id = request.data.get('collection_id')
        if not collection_id:
            return Response({'error': 'collection_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        collection = get_object_or_404(Collection, id=collection_id, user=request.user.id)
        media.collection = collection
        media.save()
        return Response({'message': f'Media {media.name} added to collection {collection.name}'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-from-collection')
    def remove_from_collection(self, request, pk=None):
        """Remove the collection association from this media instance."""
        media = self.get_object()
        media.collection = None
        media.save()
        return Response({'message': f'Media {media.name} removed from its collection'}, status=status.HTTP_200_OK)


class CollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for Collection model."""
    serializer_class = CollectionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at', 'name']
    search_fields = ['name', 'description']

    def get_queryset(self):
        """Return collections only for the requesting user."""
        return Collection.objects.filter(user=self.request.user.id)

    def perform_create(self, serializer):
        """Set `user` on collection creation to the requesting user's id."""
        serializer.save(user=self.request.user.id)

