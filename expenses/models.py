from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'

class Transaction(models.Model):
    TRANSACTION_TYPE = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPE)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.date})"
    
    class Meta:
        ordering = ['-date']

class Budget(models.Model):
    """
    Модель для бюджетов (лимитов) по категориям расходов
    """
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.PositiveSmallIntegerField()  # 1-12 для месяца
    year = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.amount} ({self.month}/{self.year})"
    
    @property
    def spent(self):
        """Расчет потраченной суммы"""
        total = Transaction.objects.filter(
            user=self.user,
            category=self.category,
            transaction_type='expense',
            date__year=self.year,
            date__month=self.month
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total
    
    @property
    def remaining(self):
        """Расчет оставшейся суммы"""
        return self.amount - self.spent
    
    @property
    def progress(self):
        """Расчет процента использования бюджета"""
        if self.amount > 0:
            return (self.spent / self.amount) * 100
        return 0
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['user', 'category', 'month', 'year']

class Goal(models.Model):
    """
    Модель для финансовых целей (например, накопить на отпуск)
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"
    
    @property
    def is_completed(self):
        """Проверка, достигнута ли цель"""
        return self.current_amount >= self.target_amount
    
    @property
    def progress(self):
        """Расчет процента выполнения цели"""
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0
    
    class Meta:
        ordering = ['deadline', 'created_at']

class GoalContribution(models.Model):
    """
    Модель для отслеживания взносов в финансовую цель
    """
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Взнос {self.amount} в {self.goal.name} ({self.date})"
    
    def save(self, *args, **kwargs):
        """Обновление текущей суммы цели при добавлении взноса"""
        super().save(*args, **kwargs)
        
        # Обновляем текущую сумму цели
        goal = self.goal
        total_contributions = GoalContribution.objects.filter(
            goal=goal
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0
        
        goal.current_amount = total_contributions
        goal.save()
    
    class Meta:
        ordering = ['-date']

class MonthlyBudgetSummary(models.Model):
    """
    Модель для сохранения итогов бюджета по месяцам
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.PositiveSmallIntegerField()  # 1-12 для месяца
    year = models.PositiveIntegerField()
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Бюджет {self.user.username} за {self.month}/{self.year}"
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['user', 'month', 'year']

class RecurringTransaction(models.Model):
    """
    Модель для повторяющихся транзакций
    """
    FREQUENCY_CHOICES = (
        ('daily', 'Ежедневно'),
        ('weekly', 'Еженедельно'),
        ('monthly', 'Ежемесячно'),
        ('quarterly', 'Ежеквартально'),
        ('yearly', 'Ежегодно'),
    )
    
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=7, choices=Transaction.TRANSACTION_TYPE)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    last_generated = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.frequency}): {self.amount}"
    
    class Meta:
        ordering = ['name']

class Attachment(models.Model):
    """
    Модель для прикрепленных файлов к транзакциям
    """
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='transaction_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Вложение для {self.transaction}"
    
    def extension(self):
        """Получить расширение файла"""
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()
    
    class Meta:
        ordering = ['-uploaded_at']