from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import CustomUserCreationForm, ProductForm
from .models import UserProfile, Product, Sale, DailyRecord
from django.contrib.auth import login

def home(request):
    return render(request, 'inventory/home.html')
    
def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, current_simulated_date=timezone.now().date())
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'inventory/signup.html', {'form': form})


@login_required
def dashboard(request):
    # Get all products owned by the current logged-in user
    products = Product.objects.filter(owner=request.user)
    # Get the user's profile to find their current simulated date
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    context = {
        'products': products,
        'simulated_date': user_profile.current_simulated_date,
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            # Create a Product instance but don't save to the database yet
            product = form.save(commit=False)
            # Assign the current logged-in user as the owner
            product.owner = request.user
            product.save()
            messages.success(request, f'Product "{product.name}" has been added successfully.')
            return redirect('dashboard')
    else:
        form = ProductForm()
    
    context = {'form': form}
    return render(request, 'inventory/add_product.html', context)