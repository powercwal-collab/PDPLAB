from io import BytesIO
from urllib.parse import quote

import oss2
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class AliyunOssStorage(Storage):
    """Minimal private/public Alibaba Cloud OSS storage for PDP uploads and evidence."""

    def __init__(self):
        auth = oss2.Auth(settings.ALIYUN_OSS_ACCESS_KEY_ID, settings.ALIYUN_OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(auth, settings.ALIYUN_OSS_ENDPOINT, settings.ALIYUN_OSS_BUCKET_NAME)

    def _open(self, name, mode="rb"):
        if mode not in {"r", "rb"}:
            raise ValueError("OSS 文件只支持只读打开")
        result = self.bucket.get_object(name)
        return File(BytesIO(result.read()), name=name)

    def _save(self, name, content):
        name = self.get_available_name(name)
        content.seek(0)
        self.bucket.put_object(name, content)
        return name

    def delete(self, name):
        if name:
            self.bucket.delete_object(name)

    def exists(self, name):
        return self.bucket.object_exists(name)

    def size(self, name):
        return self.bucket.head_object(name).content_length

    def url(self, name):
        if settings.ALIYUN_OSS_CUSTOM_DOMAIN:
            return f"https://{settings.ALIYUN_OSS_CUSTOM_DOMAIN.rstrip('/')}/{quote(name)}"
        if settings.ALIYUN_OSS_PRIVATE:
            return self.bucket.sign_url("GET", name, settings.ALIYUN_OSS_URL_EXPIRE_SECONDS)
        endpoint = settings.ALIYUN_OSS_ENDPOINT.replace("https://", "").replace("http://", "").rstrip("/")
        return f"https://{settings.ALIYUN_OSS_BUCKET_NAME}.{endpoint}/{quote(name)}"
