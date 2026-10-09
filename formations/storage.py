from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateMediaStorage(FileSystemStorage):
    """Keep paid course resources out of the public MEDIA_URL directory."""

    def __init__(self, *args, **kwargs):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)

    def url(self, name):
        return reverse('formations:private_media', kwargs={'file_path': name})