from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import FileResponse, Http404
from pathlib import Path

STATIC_ROOT = settings.BASE_DIR / 'static'

def serve_root_asset(request, filename, content_type):
    filepath = STATIC_ROOT / filename
    if not filepath.exists():
        raise Http404()
    return FileResponse(open(filepath, 'rb'), content_type=content_type)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', lambda request: serve_root_asset(request, 'sw.js', 'application/javascript')),
    path('manifest.json', lambda request: serve_root_asset(request, 'manifest.json', 'application/manifest+json')),
    path('favicon.ico', lambda request: serve_root_asset(request, 'icons/icon-192.png', 'image/png')),
    path('', include('core.urls')),
]
