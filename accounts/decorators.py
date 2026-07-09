from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.contrib.auth.mixins import AccessMixin

def role_required(allowed_roles):
    """
    Decorator to restrict access to users with specific roles in their profile.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Ensure the user has a profile and the role matches
            if hasattr(request.user, 'profile') and request.user.profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You do not have permission to access this page.")
            return redirect('catalog:book_list')
        return _wrapped_view
    return decorator

def librarian_required(view_func):
    return role_required(['LIBRARIAN'])(view_func)

def member_required(view_func):
    return role_required(['MEMBER'])(view_func)

class LibrarianRequiredMixin(AccessMixin):
    """CBV Mixin to check if the user is a Librarian."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if hasattr(request.user, 'profile') and request.user.profile.role == 'LIBRARIAN':
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access this page.")
        return redirect('catalog:book_list')

class MemberRequiredMixin(AccessMixin):
    """CBV Mixin to check if the user is a Member."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if hasattr(request.user, 'profile') and request.user.profile.role == 'MEMBER':
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "You do not have permission to access this page.")
        return redirect('catalog:book_list')
