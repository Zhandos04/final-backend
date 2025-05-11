from celery import shared_task
from django.utils import timezone
from expenses.models import Transaction
import csv
import os
from datetime import datetime, timedelta
import io

@shared_task
def generate_monthly_report(user_id):

    """
    Генерирует ежемесячный отчет пользователя (без отправки email)
    """
    from django.contrib.auth.models import User
    from expenses.models import Transaction, MonthlyBudgetSummary
    from django.db.models import Sum
    
    try:
        user = User.objects.get(id=user_id)
        
        # Получить данные за предыдущий месяц
        today = timezone.now()
        first_day = today.replace(day=1)
        last_month = first_day - timedelta(days=1)
        
        # Получить транзакции за предыдущий месяц
        transactions = Transaction.objects.filter(
            user=user,
            date__year=last_month.year,
            date__month=last_month.month
        )
        
        # Суммарные показатели

        income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expenses = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        balance = income - expenses
        
        # Сохраняем итоги месяца в БД

        summary, created = MonthlyBudgetSummary.objects.update_or_create(
            user=user,
            month=last_month.month,
            year=last_month.year,
            defaults={
                'total_income': income,
                'total_expenses': expenses,
                'balance': balance
            }
        )
        
        return f"Отчет успешно создан для пользователя {user.username} за {last_month.strftime('%B %Y')}"
    
    except User.DoesNotExist:
        return f"Пользователь с ID {user_id} не найден"
    
    except Exception as e:
        return f"Ошибка при создании отчета: {str(e)}"

@shared_task
def generate_csv_export(user_id, year=None, month=None):

    """
    Генерирует экспорт транзакций в CSV для указанного пользователя
    """
    from django.contrib.auth.models import User
    from expenses.models import Transaction
    import csv
    import io
    
    try:
        user = User.objects.get(id=user_id)
        
        # Получаем транзакции

        transactions = Transaction.objects.filter(user=user)
        
        if year:
            transactions = transactions.filter(date__year=year)

        if month:
            transactions = transactions.filter(date__month=month)
        
        transactions = transactions.order_by('-date')
        
        # Создаем CSV в памяти

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Записываем заголовки

        writer.writerow(['Дата', 'Тип', 'Категория', 'Описание', 'Сумма'])
        
        # Записываем транзакции

        for transaction in transactions:
            writer.writerow([
                transaction.date.strftime('%Y-%m-%d'),
                transaction.get_transaction_type_display(),
                transaction.category.name,
                transaction.description,
                transaction.amount
            ])
        
        # Получаем строковое представление CSV

        csv_content = output.getvalue()
        output.close()
        
        # В реальном приложении здесь бы сохраняли файл в S3 или отправляли по email
        
        return csv_content
        
    except User.DoesNotExist:
        return f"Пользователь с ID {user_id} не найден"
    except Exception as e:
        return f"Ошибка при генерации CSV: {str(e)}"

@shared_task
def process_csv_import(user_id, file_path):

    """
    Обрабатывает импорт транзакций из CSV файла
    """
    from django.contrib.auth.models import User
    from expenses.models import Transaction, Category
    import csv
    from datetime import datetime
    
    try:
        user = User.objects.get(id=user_id)
        
        transactions_created = 0
        errors = []
        
        with open(file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for row in csv_reader:
                try:

                    # Получаем или создаем категорию
                    category_name = row.get('Категория', 'Другое')
                    category, created = Category.objects.get_or_create(
                        name=category_name,
                        user=user
                    )
                    
                    # Определяем тип транзакции (по умолчанию - расход)

                    transaction_type = row.get('Тип', '').lower()
                    if 'доход' in transaction_type or 'income' in transaction_type:
                        transaction_type = 'income'

                    else:
                        transaction_type = 'expense'
                    
                    # Преобразуем дату
                    date_str = row.get('Дата', datetime.now().strftime('%Y-%m-%d'))
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            date = datetime.strptime(date_str, '%d.%m.%Y').date()

                        except ValueError:
                            date = timezone.now().date()
                    
                    # Создаем транзакцию
                    Transaction.objects.create(
                        user=user,
                        category=category,
                        transaction_type=transaction_type,
                        description=row.get('Описание', ''),
                        amount=float(row.get('Сумма', 0).replace(',', '.')),
                        date=date
                    )
                    
                    transactions_created += 1
                    
                except Exception as e:
                    errors.append(f"Ошибка в строке {csv_reader.line_num}: {str(e)}")
        
        # Удаляем временный файл, если он существует
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {
            'success': True,
            'transactions_created': transactions_created,
            'errors': errors
        }
        
    except User.DoesNotExist:
        return {
            'success': False,
            'error': f"Пользователь с ID {user_id} не найден"
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Ошибка при импорте: {str(e)}"
        }
