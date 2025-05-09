from django import forms
from .models import Transaction, Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'description', 'date', 'category', 'transaction_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': 'Enter description'}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Enter amount'}),
        }
        labels = {
            'amount': 'Amount',
            'description': 'Description',
            'date': 'Date',
            'category': 'Category',
            'transaction_type': 'Transaction Type',
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter category name'}),
        }
        labels = {
            'name': 'Category Name',
        }