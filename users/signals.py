from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile
from expenses.models import Category

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Creates profile when a user is created"""
    if created:
        # Create user profile
        Profile.objects.create(user=instance)
        
        # Create default categories for the new user
        default_expense_categories = [
            'Groceries', 'Restaurants & Cafes', 'Transport', 'Housing', 'Utilities', 
            'Internet & Communications', 'Entertainment', 'Clothing & Footwear', 'Health & Medicine', 'Education', 
            'Travel', 'Gifts', 'Household Items', 'Electronics', 'Sports', 
            'Beauty & Self-care', 'Hobbies', 'Pets', 'Taxi', 'Books'
        ]
        
        default_income_categories = [
            'Salary', 'Freelance', 'Business', 'Investments', 'Gifts',
            'Interest', 'Rental Income', 'Dividends', 'Bonuses', 'Other Income'
        ]
        
        # Create expense categories
        for category_name in default_expense_categories:
            Category.objects.create(name=category_name, user=instance)
            
        # Create income categories
        for category_name in default_income_categories:
            Category.objects.create(name=category_name, user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """Saves profile when user is saved"""
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # If profile doesn't exist, create it
        Profile.objects.create(user=instance)