from django.urls import path

from . import views

app_name = "dictionary"

urlpatterns = [
    path("customers/", views.customer_list_view, name="customers"),
    path("customers/new/", views.customer_create_view, name="customer-create"),
    path("customers/<str:customer_id>/", views.customer_detail_view, name="customer-detail"),
    path("<str:dict_type>/", views.dictionary_items_view, name="items"),
]
