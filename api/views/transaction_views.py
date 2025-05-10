from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from expenses.models import Transaction, Category
from api.serializers.transaction_serializers import TransactionSerializer
from api.throttling import UserRateThrottle, AnonRateThrottle
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone
import datetime

class TransactionViewSet(viewsets.ModelViewSet):
    """
    API для управления транзакциями пользователя.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'category', 'date']
    search_fields = ['description']
    ordering_fields = ['date', 'amount', 'category']
    ordering = ['-date']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_month(self, request):
        """Получить транзакции за указанный месяц"""
        now = timezone.now()
        year = request.query_params.get('year', now.year)
        month = request.query_params.get('month', now.month)
        
        queryset = self.get_queryset().filter(
            date__year=year,
            date__month=month
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request, category_id=None):
        """Получить транзакции по указанной категории"""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {"error": "Необходимо указать category_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        queryset = self.get_queryset().filter(category_id=category_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Получить статистику по транзакциям"""
        now = timezone.now()
        year = int(request.query_params.get('year', now.year))
        month = int(request.query_params.get('month', now.month))
        
        # Общая сумма доходов за месяц
        income = self.get_queryset().filter(
            transaction_type='income',
            date__year=year,
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Общая сумма расходов за месяц
        expenses = self.get_queryset().filter(
            transaction_type='expense',
            date__year=year,
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        return Response({
            'income': income,
            'expenses': expenses,
            'balance': income - expenses,
            'year': year,
            'month': month
        })