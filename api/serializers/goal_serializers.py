from rest_framework import serializers

# Предполагаем, что мы создадим новую модель Goal
class GoalSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    target_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    deadline = serializers.DateField(allow_null=True, required=False)
    is_completed = serializers.BooleanField(read_only=True)
    progress = serializers.FloatField(read_only=True)