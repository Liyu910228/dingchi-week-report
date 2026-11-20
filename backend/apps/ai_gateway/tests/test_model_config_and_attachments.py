import json
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.urls import reverse

from apps.ai_gateway.models import AIModelConfig
from apps.ai_gateway.services.attachments import (
    AttachmentValidationError,
    owned_attachments,
    save_uploaded_attachment,
)
from apps.ai_gateway.services.model_config import (
    load_effective_config,
    save_model_config,
    serialize_model_config,
)


@pytest.mark.django_db
def test_model_config_encrypts_key_and_never_serializes_plaintext(settings) -> None:
    result = save_model_config(
        {
            "model": "qwen-plus",
            "vision_model": "qwen-vl-plus",
            "base_url": "https://example.com/v1",
            "api_key": "secret-test-key",
        },
        user_id=1,
    )
    assert result["model"] == "qwen-plus"
    assert result["has_api_key"] is True
    assert "secret-test-key" not in json.dumps(serialize_model_config())
    assert load_effective_config().api_key == "secret-test-key"
    assert AIModelConfig.objects.count() == 1

    save_model_config(
        {"model": "qwen-plus", "api_key": "", "is_enabled": False}, user_id=1
    )
    disabled = load_effective_config()
    assert disabled.model == ""
    assert disabled.api_key == ""


@pytest.mark.django_db
def test_text_attachment_is_owner_scoped(tmp_path, settings) -> None:
    settings.MEDIA_ROOT = tmp_path
    upload = SimpleUploadedFile("work.txt", "完成客户回访\n下周跟进续约".encode())
    result = save_uploaded_attachment(upload, 100)
    assert result["kind"] == "document"
    attachment_id = int(result["id"])
    extracted = owned_attachments([attachment_id], 100)[attachment_id].extracted_text
    assert extracted.startswith("完成客户回访")
    with pytest.raises(AttachmentValidationError):
        owned_attachments([attachment_id], 200)


class ModelConfigPermissionTests(SimpleTestCase):
    @patch("apps.ai_gateway.model_config_views.require_user")
    def test_non_admin_cannot_read_model_config(self, require_user) -> None:
        from types import SimpleNamespace

        require_user.return_value = (SimpleNamespace(id=1), "delivery.manager")
        response = self.client.get(reverse("ai_gateway:model-config"))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")
