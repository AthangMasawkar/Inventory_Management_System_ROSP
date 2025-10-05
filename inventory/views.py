from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .forms import CustomUserCreationForm, ProductForm
from .models import UserProfile, Product, Sale, DailyRecord
from django.contrib.auth import login
from django.db import transaction

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


@login_required
def record_sales(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    simulated_date = user_profile.current_simulated_date
    
    # Check if a record for this day already exists
    daily_record_exists = DailyRecord.objects.filter(user=request.user, date=simulated_date).exists()
    
    if request.method == 'POST':
        if daily_record_exists:
            messages.error(request, f'Sales for {simulated_date.strftime("%Y-%m-%d")} have already been recorded.')
            return redirect('dashboard')

        # Use a transaction to ensure all or no database operations are completed
        with transaction.atomic():
            for key, value in request.POST.items():
                if key.startswith('quantity_'):
                    try:
                        product_id = int(key.split('_')[1])
                        quantity_sold = int(value)
                        
                        if quantity_sold > 0:
                            product = get_object_or_404(Product, id=product_id, owner=request.user)
                            
                            if quantity_sold <= product.quantity:
                                product.quantity -= quantity_sold
                                product.save()
                                
                                Sale.objects.create(
                                    product=product,
                                    user=request.user,
                                    quantity=quantity_sold,
                                    sale_date=simulated_date,
                                    total_price=quantity_sold * product.selling_price
                                )
                            else:
                                messages.error(request, f'Not enough stock for {product.name}. Sale not recorded.')
                                # This will roll back the transaction
                                raise Exception(f'Stock issue for {product.name}')
                    except (ValueError, IndexError, Product.DoesNotExist):
                        # Handle potential errors gracefully
                        messages.error(request, 'An error occurred while processing sales data.')
                        raise Exception('Data processing error')

            # Mark the day's sales as recorded
            DailyRecord.objects.create(user=request.user, date=simulated_date, sales_recorded=True)
        
        messages.success(request, f'Sales for {simulated_date.strftime("%Y-%m-%d")} recorded successfully.')
        return redirect('dashboard')
        
    products = Product.objects.filter(owner=request.user)
    context = {
        'products': products,
        'simulated_date': simulated_date,
        'daily_record_exists': daily_record_exists,
    }
    return render(request, 'inventory/record_sales.html', context)


@login_required
def advance_day(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    user_profile.current_simulated_date += timedelta(days=1)
    user_profile.save()
    messages.info(request, f'Time advanced to {user_profile.current_simulated_date.strftime("%Y-%m-%d")}.')
    return redirect('dashboard')

@login_required
def mark_as_holiday(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    simulated_date = user_profile.current_simulated_date
    
    # Create a record marking the day as a holiday
    DailyRecord.objects.get_or_create(user=request.user, date=simulated_date, defaults={'is_holiday': True, 'sales_recorded': True})
    
    # Automatically advance to the next day
    user_profile.current_simulated_date += timedelta(days=1)
    user_profile.save()
    
    messages.warning(request, f'{simulated_date.strftime("%Y-%m-%d")} was marked as a holiday. Time advanced to the next day.')
    return redirect('dashboard')