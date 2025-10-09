from datetime import timedelta
from django.db.models import Avg
from .models import Product, Sale

def generate_product_insights(user, simulated_date):
    products = Product.objects.filter(owner=user)
    insights = []
    
    end_date = simulated_date
    start_date = end_date - timedelta(days=14)

    for product in products:
        sales_data = Sale.objects.filter(
            product=product,
            sale_date__range=[start_date, end_date]
        )
        
        total_sales = sum(sale.quantity for sale in sales_data)
        avg_daily_sales = total_sales / 14.0 if total_sales > 0 else 0
        
        days_to_stockout = 0
        if avg_daily_sales > 0:
            days_to_stockout = product.quantity / avg_daily_sales
        

        forecasted_revenue = avg_daily_sales * float(product.selling_price) * 7
        
        
        desired_stock = avg_daily_sales * 14
        recommended_restock = 0
        if product.quantity < desired_stock:
            recommended_restock = round(desired_stock - product.quantity)

        status = "Healthy"
        status_color = "success"
        if product.quantity == 0:
            status = "Out of Stock"
            status_color = "dark"
        elif avg_daily_sales > 0 and days_to_stockout < 3:
            status = "Critical"
            status_color = "danger"
        elif product.quantity <= product.reorder_point:
            status = "Low Stock"
            status_color = "warning"
        elif total_sales == 0:
            status = "Inactive"
            status_color = "secondary"

        insights.append({
            'product': product,
            'avg_daily_sales': round(avg_daily_sales, 2),
            'days_to_stockout': round(days_to_stockout, 1),
            'status': status,
            'status_color': status_color,
            'forecasted_revenue': round(forecasted_revenue, 2),
            'recommended_restock': recommended_restock,
        })
        
    return insights