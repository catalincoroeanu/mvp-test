from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import include_docs_urls


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.products.urls")),
    path("api/v1/auth/", include('rest_framework.urls')),
    path("", include_docs_urls(title='MVP API project'))
]
