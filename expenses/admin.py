from django.contrib import admin
from .models import Category, Transaction

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date', 'category', 'transaction_type', 'user')
    list_filter = ('transaction_type', 'category', 'date', 'user')
    search_fields = ('description',)
    date_hierarchy = 'date'

admin.site.register(Category, CategoryAdmin)
admin.site.register(Transaction, TransactionAdmin)