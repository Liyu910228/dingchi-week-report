from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.api_index, name="api-index"),
    path("health/live/", views.liveness, name="liveness"),
    path("health/ready/", views.readiness, name="readiness"),
    path("security/public-key/", views.encryption_public_key, name="encryption-public-key"),
]
