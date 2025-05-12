from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Prefetch
from expenses.models import Category, Transaction
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
        # Оптимизация: используем подзапрос вместо фильтрации через related
        expense_categories = self.get_queryset().filter(
            transaction__transaction_type='expense'
        ).distinct().select_related('user')

        serializer = self.get_serializer(expense_categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def income(self, request):
        """Получить категории доходов"""
        # Оптимизация: используем подзапрос вместо фильтрации через related
        income_categories = self.get_queryset().filter(
            transaction__transaction_type='income'
        ).distinct().select_related('user')

        serializer = self.get_serializer(income_categories, many=True)
        return Response(serializer.data)