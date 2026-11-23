import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env()
env_file = Path(os.getenv("ENV_FILE", str(BASE_DIR / ".env.development")))
if env_file.is_file():
    env.read_env(env_file, overwrite=False)


def _resolve_path(value: str) -> Path:
    """Resolve .env paths: absolute paths are used as-is; relative paths use backend as root."""
    path = Path(value).expanduser()
    return path if path.is_absolute() else BASE_DIR / path


ENVIRONMENT = env("DJANGO_ENV")
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_METHODS = env.list("CORS_ALLOWED_METHODS")
CORS_ALLOW_HEADERS = env.list("CORS_ALLOW_HEADERS")
CORS_EXPOSE_HEADERS = env.list("CORS_EXPOSE_HEADERS")
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core.apps.CoreConfig",
    "apps.ai_gateway.apps.AiGatewayConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.dictionary.apps.DictionaryConfig",
    "apps.weekly_report.apps.WeeklyReportConfig",
    "apps.approvals.apps.ApprovalsConfig",
    "apps.todos.apps.TodosConfig",
]

MIDDLEWARE = [
    "apps.core.middleware.trace_id.DjangoTraceIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "apps.core.middleware.auth_context.AuthContextMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "dj_db_conn_pool.backends.mysql",
        "NAME": env("MYSQL_DATABASE"),
        "TIME_ZONE": env("MYSQL_TIME_ZONE"),
        "USER": env("MYSQL_USER"),
        "PASSWORD": env("MYSQL_PASSWORD"),
        "HOST": env("MYSQL_HOST"),
        "PORT": env.int("MYSQL_PORT"),
        # dj_db_conn_pool 已经负责底层连接复用；Django 不保留请求级持久
        # 连接，否则 ASGI 并发请求会把连接一直占在 QueuePool 中。
        "CONN_MAX_AGE": env.int("MYSQL_CONN_MAX_AGE"),
        "CONN_HEALTH_CHECKS": env.bool("MYSQL_CONN_HEALTH_CHECKS"),
        "OPTIONS": {
            "charset": env("MYSQL_CHARSET"),
            "connect_timeout": env.int("MYSQL_CONNECT_TIMEOUT"),
            "init_command": env("MYSQL_INIT_COMMAND"),
        },
        # dj_db_conn_pool uses SQLAlchemy QueuePool internally.  All pool
        # parameters are environment-driven so request code never creates
        # one-off MySQL connections.
        "POOL_OPTIONS": {
            "POOL_SIZE": env.int("MYSQL_POOL_SIZE"),
            "MAX_OVERFLOW": env.int("MYSQL_POOL_MAX_OVERFLOW"),
            "TIMEOUT": env.int("MYSQL_POOL_TIMEOUT"),
            "RECYCLE": env.int("MYSQL_POOL_RECYCLE"),
            "PRE_PING": env.bool("MYSQL_POOL_PRE_PING"),
        },
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": env.int("REDIS_POOL_MAX_CONNECTIONS"),
                "health_check_interval": env.int("REDIS_POOL_HEALTH_CHECK_INTERVAL"),
            },
            "SOCKET_CONNECT_TIMEOUT": env.int("REDIS_SOCKET_CONNECT_TIMEOUT"),
            "SOCKET_TIMEOUT": env.int("REDIS_SOCKET_TIMEOUT"),
            "IGNORE_EXCEPTIONS": env.bool("REDIS_IGNORE_EXCEPTIONS"),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = env("LANGUAGE_CODE")
TIME_ZONE = env("TIME_ZONE")
USE_I18N = env.bool("USE_I18N")
USE_TZ = env.bool("USE_TZ")

STATIC_URL = env("STATIC_URL")
STATIC_ROOT = _resolve_path(env("STATIC_ROOT"))
MEDIA_URL = env("MEDIA_URL")
MEDIA_ROOT = _resolve_path(env("MEDIA_ROOT"))
# 周报附件配置全部由环境变量控制，上传文件不直接写入任务表字段。
ATTACHMENT_MAX_SIZE_BYTES = env.int("ATTACHMENT_MAX_SIZE_BYTES")
ATTACHMENT_ALLOWED_EXTENSIONS = env.list("ATTACHMENT_ALLOWED_EXTENSIONS")
ATTACHMENT_UPLOAD_DIR = env("ATTACHMENT_UPLOAD_DIR")
DEFAULT_AUTO_FIELD = env("DEFAULT_AUTO_FIELD")

AI_API_KEY = env("AI_API_KEY")
AI_BASE_URL = env("AI_BASE_URL")
AI_MODEL = env("AI_MODEL")
AI_VISION_MODEL = env("AI_VISION_MODEL", default="qwen3-vl-plus")
AI_TIMEOUT_SECONDS = env.float("AI_TIMEOUT_SECONDS")
OCR_REQUEST_TIMEOUT_SECONDS = env.float("OCR_REQUEST_TIMEOUT_SECONDS", default=45)
OCR_POLL_TIMEOUT_SECONDS = env.float("OCR_POLL_TIMEOUT_SECONDS", default=180)

SNOWFLAKE_EPOCH_MS = env.int("SNOWFLAKE_EPOCH_MS")
SNOWFLAKE_WORKER_ID = env.int("SNOWFLAKE_WORKER_ID")
SNOWFLAKE_DATACENTER_ID = env.int("SNOWFLAKE_DATACENTER_ID")

AUTH_TOKEN_SALT = env("AUTH_TOKEN_SALT")
AUTH_TOKEN_MAX_AGE_SECONDS = env.int("AUTH_TOKEN_MAX_AGE_SECONDS")

CRYPTO_PRIVATE_KEY_PATH = _resolve_path(env("CRYPTO_PRIVATE_KEY_PATH"))
CRYPTO_PUBLIC_KEY_PATH = _resolve_path(env("CRYPTO_PUBLIC_KEY_PATH"))
CRYPTO_PRIVATE_KEY_PASSWORD = env("CRYPTO_PRIVATE_KEY_PASSWORD")
CRYPTO_KEY_SIZE = env.int("CRYPTO_KEY_SIZE")

LOG_LEVEL = env("LOG_LEVEL")
LOG_DIR = _resolve_path(env("LOG_DIR"))
LOG_FILE_NAME = env("LOG_FILE_NAME")
LOG_MAX_BYTES = env.int("LOG_MAX_BYTES")
LOG_BACKUP_COUNT = env.int("LOG_BACKUP_COUNT")
LOG_CONSOLE_ENABLED = env.bool("LOG_CONSOLE_ENABLED")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / LOG_FILE_NAME

_log_handlers = {
    "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "standard",
        "filters": ["trace_id"],
        "filename": str(LOG_FILE_PATH),
        "maxBytes": LOG_MAX_BYTES,
        "backupCount": LOG_BACKUP_COUNT,
        "encoding": "utf-8",
    },
}
_root_handlers = ["file"]
if LOG_CONSOLE_ENABLED:
    _log_handlers["console"] = {
        "class": "logging.StreamHandler",
        "formatter": "standard",
        "filters": ["trace_id"],
    }
    _root_handlers.append("console")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "trace_id": {
            "()": "apps.core.middleware.trace_id.TraceIdLogFilter",
        },
    },
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s trace_id=%(trace_id)s: %(message)s",
        }
    },
    "handlers": _log_handlers,
    "loggers": {
        # OCR 平台返回的对象存储地址带临时签名，不记录完整 HTTP 请求 URL。
        "httpx": {"level": "WARNING", "propagate": True},
        "httpcore": {"level": "WARNING", "propagate": True},
    },
    "root": {"handlers": _root_handlers, "level": LOG_LEVEL},
}
