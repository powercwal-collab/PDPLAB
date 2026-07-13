from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView
from diagnosis import views

admin.site.site_header = "PDP Lab 管理后台"
admin.site.site_title = "PDP Lab 后台"
admin.site.index_title = "数据与业务管理"

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "admin/diagnosis/integrationsettings/",
        RedirectView.as_view(url="/admin/diagnosis/aimodelsettings/", permanent=False),
        name="legacy-integration-settings",
    ),
    path(
        "admin/diagnosis/integrationsettings/<path:legacy_path>",
        RedirectView.as_view(url="/admin/diagnosis/aimodelsettings/", permanent=False),
        name="legacy-integration-settings-detail",
    ),
    path("admin/", admin.site.urls),
    path("api/", include("diagnosis.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
