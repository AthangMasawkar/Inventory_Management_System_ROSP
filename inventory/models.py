from django.db import models
from django.contrib.auth.models import User

# This model stores the user's current simulated date.
# Each user will have one entry in this table.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_simulated_date = models.DateField()

    def __str__(self):
        return f"{self.user.username}'s Profile"

# The main model for products in the inventory.
# Each product is linked to a specific user (the business owner).
class Product(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=0) # Quantity cannot be negative
    reorder_point = models.PositiveIntegerField(default=10, help_text="Quantity at which a restock alert is triggered.")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# This model records every single sale transaction.
# It links a product, the user who sold it, and the quantity.
class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    sale_date = models.DateField() # We will set this to the simulated date
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Sale of {self.quantity} x {self.product.name} on {self.sale_date}'

# This model is a simple log to track which days have been processed.
# It helps us know if sales were recorded or if it was a holiday.
class DailyRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    is_holiday = models.BooleanField(default=False)
    sales_recorded = models.BooleanField(default=False)

    class Meta:
        # Ensures a user can only have one record per date
        unique_together = ('user', 'date')

    def __str__(self):
        status = "Holiday" if self.is_holiday else "Sales Recorded" if self.sales_recorded else "Pending"
        return f'Record for {self.user.username} on {self.date}: {status}'