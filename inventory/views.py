from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .forms import CustomUserCreationForm, ProductForm
from .models import UserProfile, Product, Sale, DailyRecord
from django.contrib.auth import login
from django.db import transaction
import json
from django.db.models import Sum, F
from django.db.models.functions import TruncDay
from .utils import generate_product_insights

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
    products = Product.objects.filter(owner=request.user)
    user_profile = get_object_or_404(UserProfile, user=request.user)
    simulated_date = user_profile.current_simulated_date

    insights = generate_product_insights(request.user, simulated_date)
    alerts = [item for item in insights if item['status'] in ['Critical', 'Low Stock', 'Out of Stock']]

    sales_recorded_today = DailyRecord.objects.filter(
        user=request.user, 
        date=simulated_date
    ).exists()
    
    context = {
        'products': products,
        'simulated_date': simulated_date,
        'alerts': alerts,
        'sales_recorded_today': sales_recorded_today,
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
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
    
    daily_record_exists = DailyRecord.objects.filter(user=request.user, date=simulated_date).exists()
    
    if request.method == 'POST':
        if daily_record_exists:
            messages.error(request, f'Sales for {simulated_date.strftime("%Y-%m-%d")} have already been recorded.')
            return redirect('dashboard')

        # Using a transaction to ensure all or no database operations are completed
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
                        # Handling potential errors gracefully
                        messages.error(request, 'An error occurred while processing sales data.')
                        raise Exception('Data processing error')

            # Marking the day's sales as recorded
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
    
    DailyRecord.objects.get_or_create(user=request.user, date=simulated_date, defaults={'is_holiday': True, 'sales_recorded': True})
    
    user_profile.current_simulated_date += timedelta(days=1)
    user_profile.save()
    
    messages.warning(request, f'{simulated_date.strftime("%Y-%m-%d")} was marked as a holiday. Time advanced to the next day.')
    return redirect('dashboard')


@login_required
def visualizations(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    simulated_date = user_profile.current_simulated_date
    

    fourteen_days_ago = simulated_date - timedelta(days=14)
    sales_data = Sale.objects.filter(
        user=request.user, 
        sale_date__gte=fourteen_days_ago,
        sale_date__lte=simulated_date
    ).annotate(day=TruncDay('sale_date')).values('day').annotate(daily_total=Sum('total_price')).order_by('day')
    
    sales_labels = [s['day'].strftime('%b %d') for s in sales_data]
    sales_values = [float(s['daily_total']) for s in sales_data]


    products = Product.objects.filter(owner=request.user).order_by('-quantity')
    inventory_labels = [p.name for p in products]
    inventory_values = [p.quantity for p in products]
    

    revenue_data = Sale.objects.filter(
        user=request.user,
        sale_date__gte=fourteen_days_ago,
        sale_date__lte=simulated_date
    ).values('product__name').annotate(
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')

    pie_labels = [item['product__name'] for item in revenue_data]
    pie_values = [float(item['total_revenue']) for item in revenue_data]
    
    context = {
        'sales_labels': json.dumps(sales_labels),
        'sales_values': json.dumps(sales_values),
        'inventory_labels': json.dumps(inventory_labels),
        'inventory_values': json.dumps(inventory_values),
        'pie_labels': json.dumps(pie_labels),
        'pie_values': json.dumps(pie_values),
    }
    return render(request, 'inventory/visualizations.html', context)


@login_required
def predictions(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    simulated_date = user_profile.current_simulated_date

    insights = generate_product_insights(request.user, simulated_date)
    
    context = {
        'insights': insights
    }
    return render(request, 'inventory/predictions.html', context)


@login_required
def update_stock(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, owner=request.user)
        
        try:
            quantity_to_add = int(request.POST.get('quantity_to_add', 0))
            
            if quantity_to_add > 0:
                product.quantity += quantity_to_add
                product.save()
                messages.success(request, f'Successfully added {quantity_to_add} units to {product.name}.')
            else:
                messages.warning(request, 'Please enter a positive quantity to add.')

        except ValueError:
            messages.error(request, 'Invalid quantity entered. Please enter a number.')
            
    return redirect('dashboard')