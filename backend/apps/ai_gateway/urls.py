from django.urls import path

from . import attachment_views, model_config_views, views

app_name = "ai_gateway"

urlpatterns = [
    path("chat/", views.chat_completion, name="chat-completion"),
    path("attachments/", attachment_views.attachment_upload_view, name="attachment-upload"),
    path("model-config/", model_config_views.model_config_view, name="model-config"),
    path("model-config/save/", model_config_views.model_config_save_view, name="model-config-save"),
    path("model-config/test/", model_config_views.model_config_test_view, name="model-config-test"),
]
