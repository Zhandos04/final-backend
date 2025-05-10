from rest_framework import serializers

class MonthlySummarySerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    income_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    expense_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)

class CategoryBreakdownSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
