from rest_framework import serializers
from expenses.models import Category

class BudgetSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    progress = serializers.FloatField(read_only=True)