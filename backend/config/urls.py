from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("api/v1/todos/", include("apps.todos.urls")),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/ai/", include("apps.ai_gateway.urls")),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/dictionaries/", include("apps.dictionary.urls")),
    path("api/v1/", include("apps.weekly_report.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
