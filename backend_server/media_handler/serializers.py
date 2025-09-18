"""
media_handler.serializers

Serializers for Media and Collection models.
- MediaSerializer handles multipart file uploads, validation of media type, and
  ensures the requesting user id is attached on create via serializer context.
- CollectionSerializer includes nested (read-only) media listing.
"""

from rest_framework import serializers
from .models import Media, Collection
import logging

logger = logging.getLogger(__name__)

class MediaSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField(required=False, allow_null=True)

    class Meta:
        model = Media
        fields = [
            "id", "user", "name", "type", "size", "file", "storage_path",
            "description", "collection", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "user", "created_at", "updated_at", "size", "storage_path"
        ]

    def validate_type(self, value):
        """Validate the `type` field to be one of the allowed media types."""
        allowed = {"image", "video", "audio"}
        if value not in allowed:
            raise serializers.ValidationError(
                "Invalid media type. Allowed: image, video, audio"
            )
        return value

    def create(self, validated_data):
        """Create a Media instance with proper user assignment."""
        # Get user from request context
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Request context missing or invalid user.")
        
        user = request.user
        if not hasattr(user, 'id') or user.id is None:
            raise serializers.ValidationError("Invalid user authentication.")
        
        # Remove user from validated_data if somehow present
        validated_data.pop('user', None)
        
        # Set the user ID
        validated_data['user'] = user.id
        
        # Debug logging
        logger.info(f"Creating media with user_id: {user.id}")
        logger.info(f"Validated data: {validated_data}")
        logger.info(f"File present: {'file' in validated_data and validated_data['file'] is not None}")
        
        try:
            instance = Media.objects.create(**validated_data)
            logger.info(f"Successfully created media instance: {instance.id}")
            return instance
        except Exception as e:
            logger.error(f"Error creating media instance: {str(e)}")
            raise serializers.ValidationError(f"Failed to create media: {str(e)}")

    def update(self, instance, validated_data):
        """Perform a partial/full update."""
        return super().update(instance, validated_data)

    def get_file(self, obj):
        """Return the gateway URL for the file using dynamic IP from request."""
        if obj.file:
            # Extract type and filename from file path
            file_path = str(obj.file)
            # file_path: 'image/uuid.jpg' or 'video/uuid.mp4'
            parts = file_path.split("/", 1)
            if len(parts) == 2:
                media_type, filename = parts
                
                # Get the current request to extract the host/IP
                request = self.context.get('request')
                if request:
                    # Check for X-Forwarded-Host header (from gateway)
                    forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST')
                    if forwarded_host:
                        # Use the original host that contacted the gateway
                        if ':' in forwarded_host:
                            # Remove port and add gateway port
                            ip = forwarded_host.split(':')[0]
                            gateway_url = f"http://{ip}:3000/media/{media_type}/{filename}"
                        else:
                            # No port in host, add gateway port
                            gateway_url = f"http://{forwarded_host}:3000/media/{media_type}/{filename}"
                        return gateway_url
                    else:
                        # Fallback to request host if no forwarded host
                        host = request.get_host()
                        if ':' in host:
                            ip = host.split(':')[0]
                            gateway_url = f"http://{ip}:3000/media/{media_type}/{filename}"
                        else:
                            gateway_url = f"http://{host}:3000/media/{media_type}/{filename}"
                        return gateway_url
                else:
                    # Fallback to localhost if no request context
                    return f"http://localhost:3000/media/{media_type}/{filename}"
        return None


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection. Embeds read-only media list under `media`."""
    media = MediaSerializer(source="media_set", many=True, read_only=True)

    class Meta:
        model = Collection
        fields = [
            "id", "user", "name", "description", "media", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


