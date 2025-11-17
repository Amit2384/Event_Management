from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm, UserUpdateForm
from django.contrib.auth.forms import AuthenticationForm

def register_view(request):
    """
    Handle user registration.
    Creates new user account and profile, then logs them in automatically.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = form.save()
            
            # Set user type in profile
            user.profile.user_type = form.cleaned_data.get('user_type')
            user.profile.save()
            
            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            messages.success(request, f'Welcome to Event Management System, {username}! Your account has been created.')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'title': 'Register'
    }
    return render(request, 'authentication/register.html', context)

def login_view(request):
    """
    Handle user login.
    Authenticates user and redirects to dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                
                # Redirect to next page if specified, otherwise dashboard
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form,
        'title': 'Login'
    }
    return render(request, 'authentication/login.html', context)

@login_required
def logout_view(request):
    """
    Handle user logout.
    Logs out user and redirects to login page.
    """
    username = request.user.username
    logout(request)
    messages.info(request, f'Goodbye, {username}! You have been logged out.')
    return redirect('authentication:login')

@login_required
def profile_view(request):
    """
    Display and update user profile.
    Handles both user info and profile info updates.
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('authentication:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'My Profile'
    }
    return render(request, 'authentication/profile.html', context)