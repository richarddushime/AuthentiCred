"""
URL configuration for AuthentiCred project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Import the include() function: from django.urls import include, path
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'AuthentiCred is running',
        'timestamp': timezone.now().isoformat(),
        'environment': getattr(settings, 'DEBUG', 'Unknown')
    })

urlpatterns = [
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('wallets/', include('wallets.urls')),
    path('credentials/', include('credentials.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
