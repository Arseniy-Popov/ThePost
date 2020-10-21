from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages import views as flatpages_views
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),
    path("", include("posts.urls")),
    path(
        "about-author/",
        flatpages_views.flatpage,
        {"url": "/about-author/"},
        name="about",
    ),
    path(
        "about-tools/", flatpages_views.flatpage, {"url": "/about-tools/"}, name="tools"
    ),
    path(
        "contact-us/", flatpages_views.flatpage, {"url": "/contact-us/"}, name="contact"
    ),
]


handler404 = "posts.views._404"
handler500 = "posts.views._500"


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    import debug_toolbar

    urlpatterns += (path("__debug__/", include(debug_toolbar.urls)),)
