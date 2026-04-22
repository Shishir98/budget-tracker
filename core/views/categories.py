from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Category
from ..forms import CategoryForm


@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    form = CategoryForm()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, f'Category "{obj.name}" created.')
            return redirect('category_list')
    return render(request, 'core/categories/list.html', {'categories': categories, 'form': form})


@login_required
def category_edit(request, pk):
    obj = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('category_list')
    return render(request, 'core/categories/form.html', {'form': form, 'obj': obj})


@login_required
def category_delete(request, pk):
    obj = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Category deleted.')
    return redirect('category_list')
