from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('sw.js', serve, {'path': 'sw.js', 'document_root': settings.BASE_DIR / 'static'}),
    path('manifest.json', serve, {'path': 'manifest.json', 'document_root': settings.BASE_DIR / 'static'}),
]
