from rest_framework import serializers
from expenses.models import Transaction, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'description', 'date', 'category', 'category_name', 'transaction_type']
        read_only_fields = ['id', 'user']
