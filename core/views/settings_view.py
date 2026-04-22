from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms import UserProfileForm
from ..models import InvestmentType, Category
from ..views.investments import investment_type_list


@login_required  
def user_settings(request):
    profile = request.user.profile
    form = UserProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Settings saved.')
        return redirect('user_settings')
    return render(request, 'core/settings.html', {'form': form})
