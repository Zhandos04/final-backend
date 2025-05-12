from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from expenses.models import Transaction, Category
from api.serializers.transaction_serializers import TransactionSerializer
from api.throttling import UserRateThrottle, AnonRateThrottle
from django.db.models import Sum, F, Q, Value, Case, When, CharField, FloatField
from django.db.models.functions import ExtractMonth, ExtractYear, Coalesce
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
        return Transaction.objects.filter(user=self.request.user).select_related('category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def _get_year_month(self, request):
        """Вспомогательный метод для получения года и месяца из параметров запроса"""
        now = timezone.now()
        try:
            year = int(request.query_params.get('year', now.year))
            month = int(request.query_params.get('month', now.month))
            return year, month
        except (ValueError, TypeError):
            return now.year, now.month

    @action(detail=False, methods=['get'])
    def by_month(self, request):
        """Получить транзакции за указанный месяц"""
        year, month = self._get_year_month(request)

        queryset = self.get_queryset().filter(
            date__year=year,
            date__month=month
        ).prefetch_related('category')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Получить транзакции по указанной категории"""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {"error": "Необходимо указать category_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(category_id=category_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Получить статистику по транзакциям"""
        year, month = self._get_year_month(request)

        # Получаем статистику за один запрос с условными агрегациями
        stats = self.get_queryset().filter(
            date__year=year,
            date__month=month
        ).aggregate(
            income=Coalesce(Sum(
                Case(
                    When(transaction_type='income', then=F('amount')),
                    default=Value(0),
                    output_field=FloatField()
                )
            ), 0),
            expenses=Coalesce(Sum(
                Case(
                    When(transaction_type='expense', then=F('amount')),
                    default=Value(0),
                    output_field=FloatField()
                )
            ), 0)
        )

        return Response({
            'income': stats['income'],
            'expenses': stats['expenses'],
            'balance': stats['income'] - stats['expenses'],
            'year': year,
            'month': month
        })