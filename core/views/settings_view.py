from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from ..forms import UserProfileForm
from ..models import InvestmentType, Category


@login_required  
def user_settings(request):
    profile = request.user.profile
    
    # Profile Form
    profile_form = UserProfileForm(request.POST if 'save_profile' in request.POST else None, instance=profile)
    # Password Form
    password_form = PasswordChangeForm(request.user, request.POST if 'change_password' in request.POST else None)

    if request.method == 'POST':
        if 'save_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile settings saved.')
            return redirect('user_settings')
        
        if 'change_password' in request.POST and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('user_settings')

    return render(request, 'core/settings.html', {
        'form': profile_form,
        'password_form': password_form
    })
