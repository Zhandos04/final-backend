from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from expenses.models import Goal, GoalContribution
from api.serializers.goal_serializers import GoalSerializer
from api.throttling import UserRateThrottle
from django.utils import timezone
from django.db.models import Sum
import datetime

class GoalViewSet(viewsets.ModelViewSet):
    """
    API для управления финансовыми целями пользователя.
    """
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def progress(self, request):
        """Получить прогресс по всем целям"""
        goals = self.get_queryset()
        
        results = []
        
        for goal in goals:
            # Процент выполнения цели
            progress = goal.progress
            
            # Оставшаяся сумма
            remaining = goal.target_amount - goal.current_amount
            
            # Оставшееся время (в днях)
            days_left = None
            if goal.deadline:
                today = timezone.now().date()
                if goal.deadline > today:
                    days_left = (goal.deadline - today).days
                else:
                    days_left = 0
            
            results.append({
                'id': goal.id,
                'name': goal.name,
                'description': goal.description,
                'target_amount': goal.target_amount,
                'current_amount': goal.current_amount,
                'remaining': remaining,
                'progress': progress,
                'deadline': goal.deadline,
                'days_left': days_left,
                'is_completed': goal.is_completed
            })
        
        return Response(results)
    
    @action(detail=True, methods=['post'])
    def add_contribution(self, request, pk=None):
        """Добавить взнос к цели"""
        goal = self.get_object()
        
        amount = request.data.get('amount')
        description = request.data.get('description', '')
        date_str = request.data.get('date')
        
        # Проверяем сумму
        try:
            amount = float(amount)
            if amount <= 0:
                return Response(
                    {"error": "Сумма должна быть положительным числом"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "Недопустимая сумма"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем дату
        if date_str:
            try:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Недопустимый формат даты. Используйте YYYY-MM-DD"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            date = timezone.now().date()
        
        # Создаем взнос
        contribution = GoalContribution.objects.create(
            goal=goal,
            amount=amount,
            date=date,
            description=description
        )
        
        # Обновляем текущую сумму цели
        goal.refresh_from_db()
        
        return Response({
            'id': contribution.id,
            'goal_id': goal.id,
            'amount': amount,
            'date': date,
            'description': description,
            'goal_current_amount': goal.current_amount,
            'goal_progress': goal.progress,
            'goal_is_completed': goal.is_completed
        })
    
    @action(detail=True, methods=['get'])
    def contributions(self, request, pk=None):
        """Получить все взносы для цели"""
        goal = self.get_object()
        
        contributions = GoalContribution.objects.filter(
            goal=goal
        ).order_by('-date')
        
        results = []
        
        for contrib in contributions:
            results.append({
                'id': contrib.id,
                'amount': contrib.amount,
                'date': contrib.date,
                'description': contrib.description
            })
        
        return Response(results)