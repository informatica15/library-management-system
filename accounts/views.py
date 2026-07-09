from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import MemberSignupForm
from .models import UserProfile

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        # Redirect based on role
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'LIBRARIAN':
            return reverse('circulation:librarian_dashboard')
        return reverse('circulation:member_dashboard')

class SignUpView(CreateView):
    form_class = MemberSignupForm
    success_url = reverse_lazy('login')
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Account created successfully! You can now log in.")
        return response

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')
