from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils.deconstruct import deconstructible

if settings.USE_S3:
    from storages.backends.s3 import S3Storage as PrivateStorageBase
else:
    PrivateStorageBase = FileSystemStorage


@deconstructible
class PrivateMediaStorage(PrivateStorageBase):
    """Keep paid course resources out of the public MEDIA_URL directory."""

    def __init__(self, *args, **kwargs):
        if settings.USE_S3:
            options = {**settings.S3_STORAGE_OPTIONS, 'location': 'private', **kwargs}
            super().__init__(*args, **options)
        else:
            kwargs.setdefault('location', settings.PRIVATE_MEDIA_ROOT)
            kwargs.setdefault('base_url', None)
            super().__init__(*args, **kwargs)

    def url(self, name):
        return reverse('formations:private_media', kwargs={'file_path': name})