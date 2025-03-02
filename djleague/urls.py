from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView


admin.autodiscover()


def sentry_debug(request):
    if settings.SENTRY_ENABLED:
        division_by_zero = 1 / 0


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthcheck/", include("health_check.urls")),
    path("", include("pages.urls")),
    path("test404", TemplateView.as_view(template_name="404.html")),
    path("test403", TemplateView.as_view(template_name="403_csrf.html")),
    path("test500", TemplateView.as_view(template_name="500.html")),
    re_path(
        r"^robots.txt$",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots_file",
    ),
    path("sentry-debug/", sentry_debug),
]

if settings.DEBUG and not settings.TESTING:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
