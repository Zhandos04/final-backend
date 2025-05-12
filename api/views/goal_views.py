from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from expenses.models import Goal, GoalContribution
from api.serializers.goal_serializers import GoalSerializer
from api.throttling import UserRateThrottle
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, FloatField, Case, When, Value, DateField
from django.db.models.functions import Coalesce
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
        today = timezone.now().date()

        # Оптимизация: предварительно вычисляем все необходимые поля с помощью аннотаций
        goals = self.get_queryset().annotate(
            remaining_amount=F('target_amount') - F('current_amount'),
            days_remaining=Case(
                When(deadline__gt=today,
                     then=ExpressionWrapper(F('deadline') - today, output_field=FloatField())),
                When(deadline__lte=today, then=Value(0)),
                default=None,
                output_field=FloatField()
            )
        )

        results = []

        for goal in goals:
            results.append({
                'id': goal.id,
                'name': goal.name,
                'description': goal.description,
                'target_amount': goal.target_amount,
                'current_amount': goal.current_amount,
                'remaining': goal.remaining_amount,
                'progress': goal.progress,
                'deadline': goal.deadline,
                'days_left': int(goal.days_remaining) if goal.days_remaining is not None else None,
                'is_completed': goal.is_completed
            })

        return Response(results)

    @action(detail=True, methods=['post'])
    def add_contribution(self, request, pk=None):
        """Добавить взнос к цели"""
        goal = self.get_object()

        # Извлекаем и валидируем данные
        try:
            amount = float(request.data.get('amount', 0))
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

        description = request.data.get('description', '')
        date_str = request.data.get('date')

        # Парсим дату
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

        # Создаем взнос в одной транзакции
        contribution = GoalContribution.objects.create(
            goal=goal,
            amount=amount,
            date=date,
            description=description
        )

        # Обновляем данные цели
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

        # Оптимизация: добавляем select_related если есть связи, которые нужны
        contributions = GoalContribution.objects.filter(
            goal=goal
        ).order_by('-date').values('id', 'amount', 'date', 'description')

        # Используем values для прямого преобразования в словари
        return Response(list(contributions))