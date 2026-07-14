from pathlib import Path
import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


PDP_ENV = os.environ.get("PDP_ENV", "development").strip().lower()
IS_PRODUCTION = PDP_ENV == "production"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise ImproperlyConfigured("生产环境必须配置 DJANGO_SECRET_KEY")
    SECRET_KEY = "django-insecure-local-pdp-lab-development-only"

DEBUG = env_bool("DJANGO_DEBUG", not IS_PRODUCTION)
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost" if not IS_PRODUCTION else "",
)
if IS_PRODUCTION and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("生产环境必须配置 DJANGO_ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "" if IS_PRODUCTION else "http://127.0.0.1:4173,http://localhost:4173",
)
FRONTEND_URL = os.environ.get("PDP_FRONTEND_URL", "http://127.0.0.1:4173/")

INSTALLED_APPS = [
    "simpleui",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "diagnosis",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pdp_lab_backend.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "pdp_lab_backend.wsgi.application"
ASGI_APPLICATION = "pdp_lab_backend.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", "60")),
            conn_health_checks=True,
        ),
    }
elif IS_PRODUCTION and not env_bool("PDP_ALLOW_SQLITE_IN_PRODUCTION"):
    raise ImproperlyConfigured("生产环境必须配置 PostgreSQL DATABASE_URL")
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

REDIS_URL = os.environ.get("REDIS_URL", "")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "TIMEOUT": 300,
        },
    }
elif IS_PRODUCTION and not env_bool("PDP_ALLOW_LOCAL_CACHE_IN_PRODUCTION"):
    raise ImproperlyConfigured("生产环境必须配置 REDIS_URL")
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

AUTH_PASSWORD_VALIDATORS = [] if not IS_PRODUCTION else [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("PDP_MEDIA_ROOT", BASE_DIR / "media"))
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PDP_MEDIA_STORAGE = os.environ.get("PDP_MEDIA_STORAGE", "filesystem").strip().lower()
if PDP_MEDIA_STORAGE == "oss":
    required_oss_settings = {
        "ALIYUN_OSS_ACCESS_KEY_ID": os.environ.get("ALIYUN_OSS_ACCESS_KEY_ID", ""),
        "ALIYUN_OSS_ACCESS_KEY_SECRET": os.environ.get("ALIYUN_OSS_ACCESS_KEY_SECRET", ""),
        "ALIYUN_OSS_ENDPOINT": os.environ.get("ALIYUN_OSS_ENDPOINT", ""),
        "ALIYUN_OSS_BUCKET_NAME": os.environ.get("ALIYUN_OSS_BUCKET_NAME", ""),
    }
    missing_oss_settings = [name for name, value in required_oss_settings.items() if not value]
    if missing_oss_settings:
        raise ImproperlyConfigured(f"OSS 存储缺少配置：{', '.join(missing_oss_settings)}")
    globals().update(required_oss_settings)
    ALIYUN_OSS_CUSTOM_DOMAIN = os.environ.get("ALIYUN_OSS_CUSTOM_DOMAIN", "")
    ALIYUN_OSS_PRIVATE = env_bool("ALIYUN_OSS_PRIVATE", True)
    ALIYUN_OSS_URL_EXPIRE_SECONDS = int(os.environ.get("ALIYUN_OSS_URL_EXPIRE_SECONDS", "3600"))
    STORAGES = {
        "default": {"BACKEND": "diagnosis.storage.AliyunOssStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
elif PDP_MEDIA_STORAGE != "filesystem":
    raise ImproperlyConfigured("PDP_MEDIA_STORAGE 仅支持 filesystem 或 oss")

CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL",
    REDIS_URL or f"sqla+sqlite:///{BASE_DIR / 'celery-broker.sqlite3'}",
)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL or None)
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = int(os.environ.get("CELERY_TASK_SOFT_TIME_LIMIT", "540"))
CELERY_TASK_TIME_LIMIT = int(os.environ.get("CELERY_TASK_TIME_LIMIT", "600"))
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

PDP_DIAGNOSIS_ADAPTER = os.environ.get("PDP_DIAGNOSIS_ADAPTER", "auto")
PDP_MODEL_NAME = os.environ.get("PDP_MODEL_NAME", "gpt-5.4-mini")
PDP_AI_PROTOCOL = os.environ.get("PDP_AI_PROTOCOL", "responses")
PDP_ALLOW_MOCK_DIAGNOSIS = env_bool("PDP_ALLOW_MOCK_DIAGNOSIS")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "")
OPENAI_TIMEOUT_SECONDS = int(os.environ.get("OPENAI_TIMEOUT_SECONDS", "180"))

DATA_UPLOAD_MAX_MEMORY_SIZE = 35 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", IS_PRODUCTION)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", IS_PRODUCTION)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", IS_PRODUCTION)
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000" if IS_PRODUCTION else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", IS_PRODUCTION)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
# SimpleUI 使用同源 iframe 标签页，并会移除 Django 的 XFrame 中间件。
# 生产 Nginx 统一发送 SAMEORIGIN；因此仅静默该项由反向代理承担的检查。
X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W002"]

LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "standard"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "diagnosis": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

SIMPLEUI_HOME_INFO = False
SIMPLEUI_ANALYSIS = False
SIMPLEUI_DEFAULT_THEME = "blue.css"
SIMPLEUI_CONFIG = {
    "system_keep": True,
    "menu_display": ["PDP 诊断", "认证和授权"],
    "dynamic": True,
}
