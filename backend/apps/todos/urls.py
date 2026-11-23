from django.urls import path

from . import views

urlpatterns = [path("", views.list_view), path("<str:item_id>/read/", views.read_view)]
