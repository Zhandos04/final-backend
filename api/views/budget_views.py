from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from expenses.models import Budget, Category
from api.serializers.budget_serializers import BudgetSerializer
from api.throttling import UserRateThrottle
from django.utils import timezone
from django.db.models import Sum, F, FloatField, ExpressionWrapper, DecimalField
import datetime

class BudgetViewSet(viewsets.ModelViewSet):
    """
    API для управления бюджетами пользователя.
    """
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Получить статус выполнения всех бюджетов"""
        now = timezone.now()
        year = int(request.query_params.get('year', now.year))
        month = int(request.query_params.get('month', now.month))
        
        # Получаем бюджеты за указанный месяц
        budgets = self.get_queryset().filter(
            year=year,
            month=month
        )
        
        results = []
        
        for budget in budgets:
            # Вычисляем сумму расходов по этой категории
            spent = budget.spent
            
            # Вычисляем прогресс и оставшуюся сумму
            progress = (spent / budget.amount) * 100 if budget.amount > 0 else 0
            remaining = budget.amount - spent
            
            results.append({
                'id': budget.id,
                'name': budget.name,
                'category': budget.category.name,
                'amount': budget.amount,
                'spent': spent,
                'remaining': remaining,
                'progress': progress,
                'overspent': spent > budget.amount
            })
        
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Получить общий обзор бюджета за месяц"""
        now = timezone.now()
        year = int(request.query_params.get('year', now.year))
        month = int(request.query_params.get('month', now.month))
        
        # Общая сумма запланированного бюджета
        total_budget = self.get_queryset().filter(
            year=year,
            month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Общая сумма расходов за месяц
        from expenses.models import Transaction
        total_expenses = Transaction.objects.filter(
            user=self.request.user,
            transaction_type='expense',
            date__year=year,
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Прогресс расходования бюджета
        progress = (total_expenses / total_budget) * 100 if total_budget > 0 else 0
        
        return Response({
            'year': year,
            'month': month,
            'total_budget': total_budget,
            'total_expenses': total_expenses,
            'remaining': total_budget - total_expenses,
            'progress': progress,
            'overspent': total_expenses > total_budget
        })
