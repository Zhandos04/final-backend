from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from expenses.models import Category
from api.serializers.transaction_serializers import CategorySerializer
from api.throttling import UserRateThrottle

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API для управления категориями транзакций пользователя.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def expense(self, request):
        """Получить категории расходов"""
        # Предполагаем, что категории расходов и доходов можно различить по транзакциям
        expense_categories = self.get_queryset().filter(
            transaction__transaction_type='expense'
        ).distinct()
        
        serializer = self.get_serializer(expense_categories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def income(self, request):
        """Получить категории доходов"""
        income_categories = self.get_queryset().filter(
            transaction__transaction_type='income'
        ).distinct()
        
        serializer = self.get_serializer(income_categories, many=True)
        return Response(serializer.data)
