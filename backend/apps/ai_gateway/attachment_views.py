"""Authenticated private uploads for AI chat."""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.public import AuthenticationError, require_user
from apps.core.http import api_error, api_success, log_unhandled_exception

from .services.attachments import AttachmentValidationError, save_uploaded_attachment


@csrf_exempt
@require_POST
def attachment_upload_view(request: HttpRequest) -> JsonResponse:
    try:
        user, _role_code = require_user(request)
        upload = request.FILES.get("file")
        if upload is None:
            raise AttachmentValidationError("请选择要上传的附件。")
        result = save_uploaded_attachment(upload, int(user.id))
        return api_success(result, status=201)
    except AuthenticationError as exc:
        return api_error(exc.code, str(exc), status=401)
    except AttachmentValidationError as exc:
        return api_error("INVALID_ATTACHMENT", str(exc), status=400)
    except Exception as exc:
        log_unhandled_exception(exc, context="ai-attachment-upload")
        return api_error("INTERNAL_ERROR", "附件上传失败，请稍后重试。", status=500)
