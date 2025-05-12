from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from expenses.models import Transaction, Category
from api.serializers.report_serializers import MonthlySummarySerializer, CategoryBreakdownSerializer
from api.throttling import UserRateThrottle
from django.db.models import Sum, Count, F, FloatField, Q, Value, Case, When
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth
from django.utils import timezone
import datetime
from functools import lru_cache


class ReportViewSet(viewsets.ViewSet):
    """
    API для получения отчетов и аналитики по финансам.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def _parse_year_month(self, year=None, month=None):
        """Вспомогательный метод для обработки параметров года и месяца"""
        if not year or not month:
            now = timezone.now()
            year = year or now.year
            month = month or now.month

        return int(year), int(month)

    def get_transactions(self, year=None, month=None, start_date=None, end_date=None):
        """Вспомогательный метод для получения транзакций"""
        queryset = Transaction.objects.filter(user=self.request.user)

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        else:
            if year:
                queryset = queryset.filter(date__year=year)

            if month:
                queryset = queryset.filter(date__month=month)

        return queryset

    @action(detail=False, methods=['get'], url_path='monthly-summary/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})')
    def monthly_summary(self, request, year=None, month=None):
        """Получить месячную сводку по доходам и расходам"""
        year, month = self._parse_year_month(year, month)

        # Оптимизированный запрос с одной агрегацией
        summary = self.get_transactions(year, month).values(
            'transaction_type'
        ).annotate(
            total=Sum('amount')
        ).order_by('transaction_type')

        # Преобразуем результаты
        income = 0
        expenses = 0

        for item in summary:
            if item['transaction_type'] == 'income':
                income = item['total'] or 0
            elif item['transaction_type'] == 'expense':
                expenses = item['total'] or 0

        data = {
            'month': datetime.date(year, month, 1).strftime('%B'),
            'year': year,
            'income_total': income,
            'expense_total': expenses,
            'balance': income - expenses
        }

        serializer = MonthlySummarySerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='category-breakdown/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})')
    def category_breakdown(self, request, year=None, month=None):
        """Получить распределение расходов по категориям"""
        year, month = self._parse_year_month(year, month)

        # Получаем расходы с группировкой по категориям за один запрос
        expenses = self.get_transactions(year, month).filter(
            transaction_type='expense'
        ).values(
            'category__id', 'category__name'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')

        # Вычисляем общую сумму
        total_expenses = sum(item['total'] for item in expenses) if expenses else 0

        if total_expenses > 0:
            result = []
            for cat in expenses:
                percentage = (cat['total'] / total_expenses) * 100
                result.append({
                    'category_id': cat['category__id'],
                    'category_name': cat['category__name'],
                    'amount': cat['total'],
                    'percentage': round(percentage, 2)
                })

            serializer = CategoryBreakdownSerializer(result, many=True)
            return Response(serializer.data)

        return Response([])

    @action(detail=False, methods=['get'], url_path='yearly-comparison/(?P<year>[0-9]{4})')
    def yearly_comparison(self, request, year=None):
        """Получить сравнение доходов и расходов по месяцам за год"""
        year = int(year or timezone.now().year)

        # Оптимизированный запрос с группировкой и условными суммами
        monthly_data = self.get_transactions(year).annotate(
            month=ExtractMonth('date')
        ).values('month').annotate(
            income=Sum(Case(
                When(transaction_type='income', then=F('amount')),
                default=Value(0),
                output_field=FloatField()
            )),
            expenses=Sum(Case(
                When(transaction_type='expense', then=F('amount')),
                default=Value(0),
                output_field=FloatField()
            ))
        ).order_by('month')

        return Response(monthly_data)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Получить тренды доходов и расходов за последние 6 месяцев"""
        # Расчет периода: последние 6 месяцев
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=180)

        # Оптимизированный запрос с одной агрегацией
        monthly_data = self.get_transactions(
            start_date=start_date, end_date=end_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            income=Sum(Case(
                When(transaction_type='income', then=F('amount')),
                default=Value(0),
                output_field=FloatField()
            )),
            expenses=Sum(Case(
                When(transaction_type='expense', then=F('amount')),
                default=Value(0),
                output_field=FloatField()
            ))
        ).order_by('month')

        # Преобразуем данные в более читаемый формат
        result = []
        for item in monthly_data:
            month_str = item['month'].strftime('%b %Y')
            income = item['income'] or 0
            expenses = item['expenses'] or 0

            result.append({
                'month': month_str,
                'income': income,
                'expenses': expenses,
                'savings': income - expenses
            })

        return Response(result)

    @action(detail=False, methods=['get'])
    def savings_rate(self, request):
        """Получить ставку сбережений (savings rate) по месяцам"""
        # Последние 12 месяцев
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=365)

        # Оптимизированный запрос с одной агрегацией
        monthly_data = self.get_transactions(
            start_date=start_date, end_date=end_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            income=Sum(Case(
                When(transaction_type='income', then=F('amount')),
                default=Value(0),
                output_field=FloatField()
            )),
            expenses=Sum(Case(
                When(transaction_type='expense', then=F('amount')),
                default=Value(0),
                output_field=FloatField()
            ))
        ).order_by('month')

        # Рассчитываем ставку сбережений
        result = []
        for item in monthly_data:
            income = item['income'] or 0
            expenses = item['expenses'] or 0

            # Ставка сбережений = (Доход - Расходы) / Доход * 100%
            savings_rate = 0
            if income > 0:
                savings_rate = ((income - expenses) / income) * 100

            month_str = item['month'].strftime('%b %Y')
            result.append({
                'month': month_str,
                'income': income,
                'expenses': expenses,
                'savings_rate': round(savings_rate, 2)
            })

        return Response(result)