import os
import uuid
import mimetypes
import re
import requests
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class VercelBlobStorage(Storage):
    """Vercel Blob storage for media uploads (Django File/Image fields)."""

    api_base = "https://blob.vercel-storage.com"

    def __init__(self, token=None):
        self.token = token or os.environ.get("BLOB_READ_WRITE_TOKEN", "")

    def _safe_name(self, name):
        name = (name or "upload").replace("\\", "/").split("/")[-1]
        base, ext = os.path.splitext(name)
        base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-._") or "file"
        ext = re.sub(r"[^A-Za-z0-9.]+", "", ext)
        return f"{base}-{uuid.uuid4().hex[:8]}{ext}"

    def _save(self, name, content):
        if not self.token:
            raise ValueError("Vercel Blob upload failed: BLOB_READ_WRITE_TOKEN is not configured.")
        unique_name = self._safe_name(name)
        content_type = getattr(content, "content_type", None) or mimetypes.guess_type(unique_name)[0] or "application/octet-stream"
        try:
            data = content.read()
        except Exception:
            data = content
        resp = requests.put(
            f"{self.api_base}/{unique_name}",
            data=data,
            headers={
                "Authorization": f"Bearer {self.token}",
                "x-content-type": content_type,
            },
            timeout=30,
        )
        if not resp.ok:
            detail = ""
            try:
                detail = resp.text[:300]
            except Exception:
                detail = ""
            raise requests.HTTPError(
                f"Vercel Blob upload failed ({resp.status_code}). {detail} "
                "Check BLOB_READ_WRITE_TOKEN and that it belongs to this project's Blob store.",
                response=resp,
            )
        payload = resp.json() if resp.content else {}
        return payload.get("url") or unique_name

    def url(self, name):
        if not name:
            return ""
        if str(name).startswith(("http://", "https://")):
            return name
        return f"https://blob.vercel-storage.com/{str(name).lstrip('/')}"

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
