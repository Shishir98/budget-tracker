from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import FileResponse, Http404
from pathlib import Path
import mimetypes

STATIC_ROOT = settings.BASE_DIR / 'static'

mimetypes.init()

def serve_root_asset(request, filename):
    filepath = STATIC_ROOT / filename
    if not filepath.exists():
        raise Http404()
    content_type, _ = mimetypes.guess_type(str(filepath))
    if not content_type:
        content_type = 'application/octet-stream'
    return FileResponse(open(filepath, 'rb'), content_type=content_type)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', lambda request: serve_root_asset(request, 'sw.js')),
    path('manifest.json', lambda request: serve_root_asset(request, 'manifest.json')),
    path('favicon.ico', lambda request: serve_root_asset(request, 'icons/icon-192.png')),
    path('js/<path:filename>', lambda request, filename: serve_root_asset(request, f'js/{filename}')),
    path('icons/<path:filename>', lambda request, filename: serve_root_asset(request, f'icons/{filename}')),
    path('', include('core.urls')),
]
