from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from .forms import EmailAuthenticationForm

class SignInView(View):
    """
    Handles user authentication for the CRM system.
    Includes error handling and feedback via Django messages.
    """
    
    @method_decorator(never_cache)
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard') 
        form = EmailAuthenticationForm()
        return render(request, 'auth-signin.html', {'form': form})

    def post(self, request):
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name()}!")            
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password. Please try again.")
            return render(request, 'auth-signin.html', {'form': form})

class DashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('accounts:signin')
        return render(request, 'dashboard_placeholder.html')



class LogoutView(View):
    @method_decorator(never_cache)
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, "You have been logged out successfully.")
        return redirect('accounts:signin')