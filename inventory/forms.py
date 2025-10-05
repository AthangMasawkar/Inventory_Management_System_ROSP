from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Product

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # We only want the user to fill in these fields.
        # The 'owner' will be set automatically in the view.
        fields = ['name', 'quantity', 'reorder_point', 'selling_price']