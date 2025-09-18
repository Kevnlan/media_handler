"""
media_handler.models

Models for Media and Collection used by the backend media service.
- Collection: simple container owned by a user (reference by ID from auth service).
- Media: metadata for an uploaded media file. Files are stored on disk under MEDIA_ROOT
  and the database stores only the relative path (via FileField/storage_path).

This module provides a helper upload path builder `media_upload_path` and models with
convenience behavior to populate size and storage_path when a file is saved.
"""

import uuid
import os
from django.db import models


def media_upload_path(instance, filename):
    """
    Build upload path based on type.
    Example: media/image/<uuid>_<filename>
    """
    ext = filename.split(".")[-1]
    filename = f"{instance.id}.{ext}"
    return os.path.join(instance.type, filename)


class Collection(models.Model):
    """A grouping of media items owned by a user.

    Fields:
    - id: UUID primary key
    - user: integer id of the user from the auth service
    - name, description: human-readable metadata
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.IntegerField()  # Store user ID from auth server
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Media(models.Model):
    """Represents a media item uploaded by a user.

    Important notes:
    - The actual file is stored on disk (see `file` FileField) under MEDIA_ROOT.
    - `storage_path` stores the relative path to the stored file for quick lookup.
    - `user` stores the remote auth service user id (integer).
    - `save()` updates `size` and `storage_path` automatically when a file is present.
    """

    MEDIA_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.IntegerField()  # Store user ID from auth service
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    size = models.BigIntegerField(blank=True, null=True)
    file = models.FileField(upload_to=media_upload_path, null=True, blank=True)
    storage_path = models.CharField(max_length=500, blank=True, null=True, editable=False)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Populate size and storage_path from the uploaded file before saving."""
        if self.file:
            self.size = self.file.size
            self.storage_path = self.file.name  # This will be the correct path after upload_to
        super().save(*args, **kwargs)

    def __str__(self):
        """Return a human-readable representation of the media item."""
        return self.name
