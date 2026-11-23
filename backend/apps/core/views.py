from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .http import api_error, api_success
from .security.asymmetric import RSA_ALGORITHM, CryptoConfigurationError, get_crypto
from .services.health import check_dependencies


@require_GET
def api_index(_: HttpRequest) -> JsonResponse:
    """返回 REST API 入口索引。

    方法/路径：GET /api/v1/
    认证/权限：公开；只返回服务名称、版本和已注册的公开入口；幂等：是。
    请求参数：无。
    成功响应：200，统一 JSON 包络；data.name、data.version 为字符串，data.routes 为入口路径映射。
    失败响应：无业务失败；未知异常由统一错误处理映射为 INTERNAL_ERROR。
    追踪/兼容：响应带 X-Trace-ID；新增路由字段向后兼容，不删除既有入口说明。
    """
    return api_success(
        {
            "name": "DingChi Week Report API",
            "version": "v1",
            "routes": {
                "liveness": "/api/v1/health/live/",
                "readiness": "/api/v1/health/ready/",
                "encryption_public_key": "/api/v1/security/public-key/",
                "ai_chat": "/api/v1/ai/chat/",
                "mcp": "/mcp/",
            },
        }
    )


@require_GET
def liveness(_: HttpRequest) -> JsonResponse:
    """检查 Web 服务进程是否存活。

    方法/路径：GET /api/v1/health/live/
    认证/权限：公开健康探针；不读取业务数据；幂等：是。
    请求参数：无。
    成功响应：200，data.status 固定为 ok，data.service 和 data.environment 为字符串，
      data.timestamp 为带时区 ISO 8601 时间。
    失败响应：服务无法处理请求时由统一错误处理返回 INTERNAL_ERROR。
    追踪/兼容：响应带 X-Trace-ID；响应字段只增不改，时间格式保持 ISO 8601。
    """
    return api_success(
        {
            "status": "ok",
            "service": "dingchi-week-report-backend",
            "environment": settings.ENVIRONMENT,
            "timestamp": timezone.now().isoformat(),
        }
    )


@require_GET
def readiness(_: HttpRequest) -> JsonResponse:
    """检查数据库、Redis 等依赖是否达到接流量条件。

    方法/路径：GET /api/v1/health/ready/
    认证/权限：公开健康探针；不返回连接凭据或内部地址；幂等：是。
    请求参数：无。
    成功响应：200，data.status 为 ok，data.checks 为依赖名称到 ok 状态的映射。
    失败响应：503，data.status 为 degraded，data.checks 仅包含脱敏后的依赖状态；不返回异常堆栈。
    追踪/兼容：响应带 X-Trace-ID；checks 可新增依赖键，既有键的状态语义保持不变。
    """
    checks = check_dependencies()
    ready = all(value == "ok" for value in checks.values())
    return api_success(
        {"status": "ok" if ready else "degraded", "checks": checks},
        status=200 if ready else 503,
    )


@require_GET
def encryption_public_key(_: HttpRequest) -> JsonResponse:
    """返回浏览器加密页面密码所需的 RSA 公钥。

    方法/路径：GET /api/v1/security/public-key/
    认证/权限：公开；只返回公钥和算法标识，绝不返回私钥；幂等：是。
    请求参数：无。
    成功响应：200，data.algorithm 固定为 RSA-OAEP-SHA256，
      data.public_key 为 SubjectPublicKeyInfo PEM。
    失败响应：503 CRYPTO_NOT_CONFIGURED；只返回安全提示，不暴露密钥路径或配置详情。
    追踪/兼容：响应带 X-Trace-ID；算法字段和密文前缀属于版本契约，轮换时保留兼容策略。
    """
    try:
        public_key = get_crypto().public_key_pem()
    except CryptoConfigurationError:
        return api_error(
            "CRYPTO_NOT_CONFIGURED",
            "密码加密服务尚未配置。",
            status=503,
        )
    return api_success({"algorithm": RSA_ALGORITHM, "public_key": public_key})
