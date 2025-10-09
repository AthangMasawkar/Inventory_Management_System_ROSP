from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import UserProfile
from .utils import generate_product_insights

@shared_task
def check_stock_and_send_alerts():
    users = User.objects.all()

    for user in users:
        try:
            user_profile = UserProfile.objects.get(user=user)
            simulated_date = user_profile.current_simulated_date

            insights = generate_product_insights(user, simulated_date)
            alerts = [item for item in insights if item['status'] in ['Critical', 'Low Stock', 'Out of Stock']]

            if alerts and user.email:
                subject = f'Inventory Alert for {simulated_date.strftime("%Y-%m-%d")}'
                message_body = 'Hello,\n\nThis is an automated alert from InventoryPro. The following items in your inventory require attention:\n\n'

                for alert in alerts:
                    product = alert['product']
                    message_body += f"- {product.name}: Status is {alert['status']}. Current stock: {product.quantity}. (Est. {alert['days_to_stockout']} days left)\n"

                message_body += "\nPlease log in to your dashboard to restock these items.\n\nThank you,\nThe InventoryPro Team"

                send_mail(
                    subject,
                    message_body,
                    None,
                    [user.email],
                    fail_silently=False,
                )
        except UserProfile.DoesNotExist:
            continue
    return f'Alert check completed for {users.count()} users.'