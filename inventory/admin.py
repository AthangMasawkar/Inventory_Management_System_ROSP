from django.contrib import admin
from .models import UserProfile, Product, Sale, DailyRecord

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_simulated_date')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'quantity', 'reorder_point', 'selling_price')
    list_filter = ('owner',)
    search_fields = ('name',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'quantity', 'total_price', 'sale_date')
    list_filter = ('user', 'sale_date')

@admin.register(DailyRecord)
class DailyRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'sales_recorded', 'is_holiday')
    list_filter = ('user', 'date', 'is_holiday')