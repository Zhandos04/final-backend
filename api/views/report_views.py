from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from expenses.models import Transaction, Category
from api.serializers.report_serializers import MonthlySummarySerializer, CategoryBreakdownSerializer
from api.throttling import UserRateThrottle
from django.db.models import Sum, Count, F, FloatField
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth
from django.utils import timezone
import datetime

class ReportViewSet(viewsets.ViewSet):
    """
    API для получения отчетов и аналитики по финансам.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_transactions(self, year=None, month=None):
        """Вспомогательный метод для получения транзакций"""
        queryset = Transaction.objects.filter(user=self.request.user)
        
        if year:
            queryset = queryset.filter(date__year=year)
        
        if month:
            queryset = queryset.filter(date__month=month)
            
        return queryset
    
    @action(detail=False, methods=['get'], url_path='monthly-summary/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})')
    def monthly_summary(self, request, year=None, month=None):
        """Получить месячную сводку по доходам и расходам"""
        if not year or not month:
            now = timezone.now()
            year = now.year
            month = now.month
        
        year = int(year)
        month = int(month)
        
        # Получаем транзакции за указанный месяц
        transactions = self.get_transactions(year, month)
        
        # Рассчитываем общие суммы
        income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        balance = income - expenses
        
        data = {
            'month': datetime.date(year, month, 1).strftime('%B'),
            'year': year,
            'income_total': income,
            'expense_total': expenses,
            'balance': balance
        }
        
        serializer = MonthlySummarySerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='category-breakdown/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})')
    def category_breakdown(self, request, year=None, month=None):
        """Получить распределение расходов по категориям"""
        if not year or not month:
            now = timezone.now()
            year = now.year
            month = now.month
        
        year = int(year)
        month = int(month)
        
        # Получаем транзакции расходов за указанный месяц
        transactions = self.get_transactions(year, month).filter(transaction_type='expense')
        
        # Общая сумма расходов
        total_expenses = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        
        if total_expenses > 0:
            # Группируем по категориям
            categories = transactions.values(
                'category__id', 'category__name'
            ).annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            result = []
            for cat in categories:
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
        if not year:
            now = timezone.now()
            year = now.year
        
        year = int(year)
        
        # Получаем транзакции за указанный год
        transactions = self.get_transactions(year)
        
        # Группируем по месяцам и типу транзакции
        monthly_data = transactions.annotate(
            month=ExtractMonth('date')
        ).values(
            'month'
        ).annotate(
            income=Sum('amount', filter=F('transaction_type') == 'income'),
            expenses=Sum('amount', filter=F('transaction_type') == 'expense')
        ).order_by('month')
        
        return Response(monthly_data)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Получить тренды доходов и расходов за последние 6 месяцев"""
        # Последние 6 месяцев
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=180)
        
        # Получаем транзакции за этот период
        transactions = Transaction.objects.filter(
            user=self.request.user,
            date__range=[start_date, end_date]
        )
        
        # Группировка по месяцам
        monthly_data = transactions.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            income=Sum('amount', filter=F('transaction_type') == 'income'),
            expenses=Sum('amount', filter=F('transaction_type') == 'expense'),
            savings=Sum(
                F('amount') * (1 if F('transaction_type') == 'income' else -1),
                output_field=FloatField()
            )
        ).order_by('month')
        
        # Преобразуем данные в более читаемый формат
        result = []
        for item in monthly_data:
            month_str = item['month'].strftime('%b %Y')
            result.append({
                'month': month_str,
                'income': item['income'] or 0,
                'expenses': item['expenses'] or 0,
                'savings': item['savings'] or 0
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def savings_rate(self, request):
        """Получить ставку сбережений (savings rate) по месяцам"""
        # Последние 12 месяцев
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=365)
        
        # Получаем транзакции за этот период
        transactions = Transaction.objects.filter(
            user=self.request.user,
            date__range=[start_date, end_date]
        )
        
        # Группировка по месяцам
        monthly_data = transactions.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            income=Sum('amount', filter=F('transaction_type') == 'income'),
            expenses=Sum('amount', filter=F('transaction_type') == 'expense')
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