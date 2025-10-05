from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_product/', views.add_product, name='add_product'),
    path('record_sales/', views.record_sales, name='record_sales'),
    path('advance_day/', views.advance_day, name='advance_day'),
    path('mark_as_holiday/', views.mark_as_holiday, name='mark_as_holiday'),
    path('visualizations/', views.visualizations, name='visualizations'),
    path('predictions/', views.predictions, name='predictions'),
    path('update_stock/<int:product_id>/', views.update_stock, name='update_stock'),
]