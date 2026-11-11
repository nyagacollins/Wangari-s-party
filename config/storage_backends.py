import os
import uuid
import mimetypes
import requests
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class VercelBlobStorage(Storage):
    """Vercel Blob storage for media uploads (Django File/Image fields)."""

    api_base = "https://blob.vercel-storage.com"

    def __init__(self, token=None):
        self.token = token or os.environ.get("BLOB_READ_WRITE_TOKEN", "")

    def _headers(self, content_type=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        if content_type:
            headers["x-content-type"] = content_type
        return headers

    def _save(self, name, content):
        base, ext = os.path.splitext(name)
        unique_name = f"{base}-{uuid.uuid4().hex[:8]}{ext}".lstrip("/")
        content_type = getattr(content, "content_type", None) or mimetypes.guess_type(unique_name)[0] or "application/octet-stream"
        data = content.read()
        resp = requests.put(
            f"{self.api_base}/{unique_name}",
            data=data,
            headers=self._headers(content_type),
            params={"access": "public"},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json() if resp.content else {}
        return payload.get("url") or unique_name

    def url(self, name):
        if not name:
            return ""
        if name.startswith("http://") or name.startswith("https://"):
            return name
        return f"https://blob.vercel-storage.com/{name.lstrip('/')}"

    def exists(self, name):
        return False

    def size(self, name):
        return 0

    def delete(self, name):
        if not self.token or not name or not str(name).startswith("http"):
            return
        try:
            requests.post(
                f"{self.api_base}/delete",
                json={"urls": [name]},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=15,
            )
        except Exception:
            pass
