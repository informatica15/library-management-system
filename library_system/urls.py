from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def root_redirect(request):
    """Redirect root access to catalog or login based on auth status."""
    if request.user.is_authenticated:
        return redirect('catalog:book_list')
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Redirect root URL
    path('', root_redirect, name='root_redirect'),
    # Mount app URLs
    path('accounts/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('circulation/', include('circulation.urls')),
]
